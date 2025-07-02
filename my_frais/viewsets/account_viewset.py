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
    API endpoints pour gérer les comptes bancaires.

    list:
        Retourne la liste des comptes de l'utilisateur connecté.
        Les administrateurs peuvent voir tous les comptes.
        Supporte le filtrage, la recherche et le tri.

    create:
        Crée un nouveau compte bancaire.
        L'utilisateur connecté sera automatiquement défini comme propriétaire.

    retrieve:
        Retourne les détails d'un compte spécifique.

    update:
        Met à jour un compte existant complètement.
        Tous les champs doivent être fournis.

    partial_update:
        Met à jour un compte existant partiellement.
        Seuls les champs fournis seront mis à jour.

    delete:
        Supprime un compte existant.

    Filtres disponibles:
        - user: ID de l'utilisateur propriétaire
        - created_by: ID de l'utilisateur créateur

    Champs de recherche:
        - user__username: Nom d'utilisateur du propriétaire
        - user__email: Email du propriétaire

    Champs de tri:
        - solde: Solde du compte
        - created_at: Date de création
        - updated_at: Date de mise à jour
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
        """Filtrer les comptes selon l'utilisateur connecté avec optimisation"""
        user = self.request.user
        if user.is_staff:
            return Account.objects.select_related('user', 'created_by').all()
        return Account.objects.select_related('user', 'created_by').filter(user=user)
    
    def get_serializer_class(self):
        """Utiliser le serializer approprié selon l'action"""
        if self.action == 'list':
            return AccountListSerializer
        return AccountSerializer
    
    def create(self, request, *args, **kwargs):
        """Créer un compte avec debug des erreurs 400"""
        print(f"🔵 POST /accounts/ - Données reçues:")
        print(f"📋 Body: {request.data}")
        print(f"👤 User: {request.user}")
        print(f"🔑 Auth: {request.auth}")
        
        serializer = self.get_serializer(data=request.data)
        
        if not serializer.is_valid():
            print(f"❌ ERREUR 400 - Validation échouée:")
            print(f"📝 Erreurs: {serializer.errors}")
            print(f"📊 Données reçues: {request.data}")
            print(f"🎯 Champs requis: {self.get_serializer().Meta.model._meta.get_fields()}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        print(f"✅ SUCCÈS - Account créé: ID {serializer.data.get('id')}")
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def perform_create(self, serializer):
        """Créer un compte avec l'utilisateur connecté comme créateur"""
        serializer.save(created_by=self.request.user)
    
    def perform_update(self, serializer):
        """Mettre à jour un compte"""
        serializer.save()
    
    def perform_destroy(self, instance):
        """Supprimer un compte (les entités liées seront supprimées automatiquement via CASCADE)"""
        instance.delete()
    
    @action(detail=True, methods=['get'])
    def operations(self, request, pk=None):
        """
        Retourne toutes les opérations d'un compte.

        Fournit la liste complète des opérations associées à un compte spécifique,
        triées par date de création décroissante.

        Parameters:
            pk (int): L'identifiant du compte

        Returns:
            Response: Liste des opérations avec des informations sur le compte
        """
        account = self.get_object()
        operations = account.operations.select_related('created_by').all().order_by('-created_at')
        
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
        """
        Retourne les statistiques d'un compte.

        Fournit des statistiques détaillées sur un compte spécifique, incluant :
        - Statistiques des opérations
        - Statistiques par période (30 jours)
        - Informations sur les prélèvements automatiques

        Parameters:
            pk (int): L'identifiant du compte

        Returns:
            Response: Statistiques détaillées du compte
        """
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
        """
        Ajuste manuellement le solde d'un compte.

        Permet de modifier le solde d'un compte et crée une opération
        d'ajustement correspondante.

        Parameters:
            pk (int): L'identifiant du compte

        Request Body:
            {
                "montant": decimal,
                "raison": str (optionnel)
            }

        Returns:
            Response: Détails de l'ajustement effectué
        """
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
            ancien_solde = account.solde
            account.solde += montant_decimal
            account.save()
            
            # Créer une opération d'ajustement
            from my_frais.models import Operation
            operation_created = Operation.objects.create(
                compte_reference=account,
                montant=montant_decimal,
                description=f"Ajustement: {raison}",
                created_by=request.user
            )
            
            return Response({
                'ajustement': float(montant_decimal),
                'ancien_solde': float(ancien_solde),
                'nouveau_solde': float(account.solde),
                'operation_created': True
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
        comptes_positifs = total_comptes - comptes_negatifs
        
        # Détails des comptes
        comptes_details = []
        for compte in accounts:
            operations_count = compte.operations.count()
            comptes_details.append({
                'id': compte.id,
                'nom': compte.nom,
                'solde': float(compte.solde),
                'operations_count': operations_count
            })
        
        return Response({
            'total_comptes': total_comptes,
            'total_solde': float(total_solde),
            'comptes_positifs': comptes_positifs,
            'comptes_negatifs': comptes_negatifs,
            'comptes': comptes_details
        })

    @action(detail=False, methods=['get'])
    def global_overview(self, request):
        """
        Vue d'ensemble complète des comptes pour le dashboard.

        Fournit une vue globale de tous les comptes accessibles, incluant :
        - Statistiques de base (soldes, nombre de comptes)
        - Détails par compte
        - Statistiques d'activité récente
        - Informations sur les prélèvements et revenus
        - Alertes importantes

        Returns:
            Response: Vue d'ensemble complète des comptes
        """
        accounts = self.get_queryset()
        
        # Statistiques de base
        total_solde = accounts.aggregate(total=Sum('solde'))['total'] or Decimal('0.00')
        total_comptes = accounts.count()
        comptes_negatifs = accounts.filter(solde__lt=0)
        comptes_positifs = accounts.filter(solde__gte=0)
        
        # Calculs détaillés par compte
        comptes_details = []
        total_operations = 0
        derniere_activite_globale = None
        
        for compte in accounts:
            compte_operations = compte.operations.all()
            operations_count = compte_operations.count()
            total_operations += operations_count
            
            derniere_operation = compte_operations.order_by('-created_at').first()
            if derniere_operation:
                if derniere_activite_globale is None or derniere_operation.created_at > derniere_activite_globale:
                    derniere_activite_globale = derniere_operation.created_at
            
            comptes_details.append({
                'id': compte.id,
                'nom': compte.nom,
                'solde': float(compte.solde),
                'nombre_operations': operations_count,
                'derniere_activite': derniere_operation.created_at.isoformat() if derniere_operation else None,
                'status': 'positif' if compte.solde >= 0 else 'negatif'
            })
        
        # Statistiques d'activité récente
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        from my_frais.models import Operation
        user = request.user
        if user.is_staff:
            operations_7_jours = Operation.objects.filter(created_at__date__gte=week_ago).count()
            operations_30_jours = Operation.objects.filter(created_at__date__gte=month_ago).count()
        else:
            operations_7_jours = Operation.objects.filter(compte_reference__user=user, created_at__date__gte=week_ago).count()
            operations_30_jours = Operation.objects.filter(compte_reference__user=user, created_at__date__gte=month_ago).count()
        
        # Prélèvements et revenus actifs
        from my_frais.models import DirectDebit, RecurringIncome
        if user.is_staff:
            prelevements_actifs = DirectDebit.objects.filter(actif=True).count()
            revenus_actifs = RecurringIncome.objects.filter(actif=True).count()
        else:
            prelevements_actifs = DirectDebit.objects.filter(compte_reference__user=user, actif=True).count()
            revenus_actifs = RecurringIncome.objects.filter(compte_reference__user=user, actif=True).count()
        
        # Alertes
        alertes = []
        if comptes_negatifs.count() > 0:
            alertes.append(f"{comptes_negatifs.count()} compte(s) en déficit")
        
        # Prélèvements imminents (dans les 7 prochains jours)
        date_limite = today + timedelta(days=7)
        prelevements_imminents = 0
        if user.is_staff:
            prelevements_imminents = DirectDebit.objects.filter(
                actif=True, 
                date_prelevement__lte=date_limite
            ).count()
        else:
            prelevements_imminents = DirectDebit.objects.filter(
                compte_reference__user=user,
                actif=True, 
                date_prelevement__lte=date_limite
            ).count()
        
        if prelevements_imminents > 0:
            alertes.append(f"{prelevements_imminents} prélèvement(s) dans les 7 prochains jours")
        
        return Response({
            'summary': {
                'total_comptes': total_comptes,
                'total_solde': float(total_solde),
                'comptes_positifs': comptes_positifs.count(),
                'comptes_negatifs': comptes_negatifs.count()
            },
            'recent_activity': {
                'operations_7_jours': operations_7_jours,
                'operations_30_jours': operations_30_jours,
                'prélèvements_actifs': prelevements_actifs,
                'revenus_actifs': revenus_actifs
            },
            'alerts': {
                'comptes_negatifs': comptes_negatifs.count(),
                'prélèvements_imminents': prelevements_imminents,
                'messages': alertes
            },
            'comptes': comptes_details
        }) 