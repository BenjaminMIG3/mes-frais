from rest_framework import viewsets, status, filters, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Count
from datetime import datetime, timedelta
from decimal import Decimal

from my_frais.models import Account
from my_frais.serializers.account_serializer import AccountSerializer, AccountListSerializer


class AccountViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des comptes bancaires.
    
    Permet de créer, lire, mettre à jour et supprimer des comptes.
    Inclut des actions personnalisées pour les statistiques et la gestion du solde.
    """
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['user', 'created_by']
    search_fields = ['user__username', 'user__email']
    ordering_fields = ['solde', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filtrer les comptes selon l'utilisateur connecté"""
        user = self.request.user
        if user.is_staff:
            return Account.objects.all()
        return Account.objects.filter(user=user)
    
    def get_serializer_class(self):
        """Utiliser le serializer approprié selon l'action"""
        if self.action == 'list':
            return AccountListSerializer
        return AccountSerializer
    
    def perform_create(self, serializer):
        """Créer un compte avec l'utilisateur connecté comme créateur"""
        serializer.save(created_by=self.request.user)
    
    def perform_update(self, serializer):
        """Mettre à jour un compte"""
        serializer.save()
    
    def perform_destroy(self, instance):
        """Supprimer un compte avec vérification"""
        # Vérifier qu'il n'y a pas d'opérations liées
        if instance.operations.exists():
            raise serializers.ValidationError(
                "Impossible de supprimer un compte avec des opérations. "
                "Supprimez d'abord toutes les opérations."
            )
        instance.delete()
    
    @action(detail=True, methods=['get'])
    def operations(self, request, pk=None):
        """Récupérer toutes les opérations d'un compte"""
        account = self.get_object()
        operations = account.operations.all().order_by('-created_at')
        
        from my_frais.serializers.operation_serializer import OperationListSerializer
        serializer = OperationListSerializer(operations, many=True)
        
        return Response({
            'account_id': account.id,
            'account_username': account.user.username,
            'operations': serializer.data,
            'total_operations': operations.count()
        })
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Obtenir les statistiques d'un compte"""
        account = self.get_object()
        
        # Statistiques des opérations
        operations = account.operations.all()
        total_operations = operations.count()
        total_montant = operations.aggregate(total=Sum('montant'))['total'] or 0
        
        # Statistiques par période
        today = datetime.now().date()
        month_ago = today - timedelta(days=30)
        
        operations_month = operations.filter(created_at__date__gte=month_ago)
        montant_month = operations_month.aggregate(total=Sum('montant'))['total'] or 0
        
        # Prélèvements automatiques  
        direct_debits = account.operations.filter(directdebit__actif=True, directdebit__isnull=False)
        total_direct_debits = direct_debits.count()
        montant_direct_debits = direct_debits.aggregate(total=Sum('montant'))['total'] or 0
        
        return Response({
            'account_id': account.id,
            'account_username': account.user.username,
            'solde_actuel': float(account.solde),
            'statistics': {
                'total_operations': total_operations,
                'total_montant_operations': float(total_montant),
                'operations_30_jours': operations_month.count(),
                'montant_30_jours': float(montant_month),
                'prélèvements_actifs': total_direct_debits,
                'montant_prélèvements': float(montant_direct_debits)
            }
        })
    
    @action(detail=True, methods=['post'])
    def adjust_balance(self, request, pk=None):
        """Ajuster manuellement le solde d'un compte"""
        account = self.get_object()
        montant = request.data.get('montant')
        raison = request.data.get('raison', 'Ajustement manuel')
        
        if montant is None:
            return Response(
                {'error': 'Le montant est requis'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            montant_decimal = Decimal(str(montant))
            account.solde += montant_decimal
            account.save()
            
            # Créer une opération d'ajustement
            from my_frais.models import Operation
            Operation.objects.create(
                compte_reference=account,
                montant=montant_decimal,
                description=f"Ajustement: {raison}",
                created_by=request.user
            )
            
            return Response({
                'message': 'Solde ajusté avec succès',
                'nouveau_solde': float(account.solde),
                'ajustement': float(montant_decimal)
            })
            
        except (ValueError, TypeError):
            return Response(
                {'error': 'Montant invalide'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Résumé de tous les comptes de l'utilisateur"""
        accounts = self.get_queryset()
        
        total_solde = accounts.aggregate(total=Sum('solde'))['total'] or 0
        total_comptes = accounts.count()
        
        # Comptes avec solde négatif
        comptes_negatifs = accounts.filter(solde__lt=0).count()
        
        return Response({
            'total_comptes': total_comptes,
            'total_solde': float(total_solde),
            'comptes_negatifs': comptes_negatifs,
            'comptes_positifs': total_comptes - comptes_negatifs
        }) 