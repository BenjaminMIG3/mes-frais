from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Count, Q
from datetime import datetime, timedelta, date
from decimal import Decimal

from my_frais.models import DirectDebit, Account
from my_frais.serializers.direct_debit_serializer import (
    DirectDebitSerializer, 
    DirectDebitListSerializer,
    DirectDebitSummarySerializer
)


class DirectDebitViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des prélèvements automatiques.
    
    Permet de créer, lire, mettre à jour et supprimer des prélèvements automatiques.
    Inclut des actions personnalisées pour la gestion des échéances et des statistiques.
    """
    queryset = DirectDebit.objects.all()
    serializer_class = DirectDebitSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['compte_reference', 'created_by']
    search_fields = ['description']
    ordering_fields = ['montant', 'date_prelevement', 'echeance', 'created_at']
    ordering = ['date_prelevement']
    
    def get_queryset(self):
        """Filtrer les prélèvements selon l'utilisateur connecté"""
        user = self.request.user
        if user.is_staff:
            return DirectDebit.objects.all()
        return DirectDebit.objects.filter(compte_reference__user=user)
    
    def get_serializer_class(self):
        """Utiliser le serializer approprié selon l'action"""
        if self.action == 'list':
            return DirectDebitListSerializer
        elif self.action == 'summary':
            return DirectDebitSummarySerializer
        return DirectDebitSerializer
    
    def perform_create(self, serializer):
        """Créer un prélèvement automatique avec l'utilisateur connecté comme créateur"""
        serializer.save(created_by=self.request.user)
    
    def perform_update(self, serializer):
        """Mettre à jour un prélèvement automatique"""
        serializer.save()
    
    def perform_destroy(self, instance):
        """Supprimer un prélèvement automatique"""
        instance.delete()
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Obtenir tous les prélèvements actifs"""
        today = date.today()
        active_debits = self.get_queryset().filter(
            Q(echeance__isnull=True) | Q(echeance__gte=today)
        ).order_by('date_prelevement')
        
        serializer = DirectDebitListSerializer(active_debits, many=True)
        return Response({
            'active_count': active_debits.count(),
            'prélèvements_actifs': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def expired(self, request):
        """Obtenir tous les prélèvements expirés"""
        today = date.today()
        expired_debits = self.get_queryset().filter(
            echeance__lt=today
        ).order_by('-echeance')
        
        serializer = DirectDebitListSerializer(expired_debits, many=True)
        return Response({
            'expired_count': expired_debits.count(),
            'prélèvements_expirés': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Obtenir les prélèvements à venir dans les 30 prochains jours"""
        today = date.today()
        thirty_days_later = today + timedelta(days=30)
        
        upcoming_debits = self.get_queryset().filter(
            date_prelevement__gte=today,
            date_prelevement__lte=thirty_days_later
        ).order_by('date_prelevement')
        
        serializer = DirectDebitListSerializer(upcoming_debits, many=True)
        return Response({
            'upcoming_count': upcoming_debits.count(),
            'prélèvements_à_venir': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Obtenir les statistiques des prélèvements automatiques"""
        direct_debits = self.get_queryset()
        today = date.today()
        
        # Statistiques générales
        total_debits = direct_debits.count()
        total_montant = direct_debits.aggregate(total=Sum('montant'))['total'] or Decimal('0.00')
        
        # Prélèvements actifs
        active_debits = direct_debits.filter(
            Q(echeance__isnull=True) | Q(echeance__gte=today)
        )
        active_count = active_debits.count()
        active_montant = active_debits.aggregate(total=Sum('montant'))['total'] or Decimal('0.00')
        
        # Prélèvements expirés
        expired_debits = direct_debits.filter(echeance__lt=today)
        expired_count = expired_debits.count()
        expired_montant = expired_debits.aggregate(total=Sum('montant'))['total'] or Decimal('0.00')
        
        # Prélèvements ce mois
        month_start = today.replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        this_month_debits = direct_debits.filter(
            date_prelevement__gte=month_start,
            date_prelevement__lte=month_end
        )
        this_month_count = this_month_debits.count()
        this_month_montant = this_month_debits.aggregate(total=Sum('montant'))['total'] or Decimal('0.00')
        
        return Response({
            'statistics': {
                'total_prélèvements': total_debits,
                'total_montant': float(total_montant),
                'prélèvements_actifs': active_count,
                'montant_actifs': float(active_montant),
                'prélèvements_expirés': expired_count,
                'montant_expirés': float(expired_montant),
                'prélèvements_ce_mois': this_month_count,
                'montant_ce_mois': float(this_month_montant)
            }
        })
    
    @action(detail=False, methods=['get'])
    def by_account(self, request):
        """Obtenir les prélèvements groupés par compte"""
        direct_debits = self.get_queryset()
        
        # Grouper par compte
        accounts_data = {}
        for debit in direct_debits:
            account_id = debit.compte_reference.id
            account_username = debit.compte_reference.user.username
            
            if account_id not in accounts_data:
                accounts_data[account_id] = {
                    'account_id': account_id,
                    'account_username': account_username,
                    'prélèvements_count': 0,
                    'total_montant': Decimal('0.00'),
                    'prélèvements_actifs': 0,
                    'prélèvements_expirés': 0,
                    'prélèvements': []
                }
            
            accounts_data[account_id]['prélèvements_count'] += 1
            accounts_data[account_id]['total_montant'] += debit.montant
            
            # Compter les statuts
            if debit.echeance and debit.echeance < date.today():
                accounts_data[account_id]['prélèvements_expirés'] += 1
            else:
                accounts_data[account_id]['prélèvements_actifs'] += 1
            
            accounts_data[account_id]['prélèvements'].append({
                'id': debit.id,
                'montant': float(debit.montant),
                'description': debit.description,
                'date_prelevement': debit.date_prelevement,
                'echeance': debit.echeance,
                'is_active': debit.echeance is None or debit.echeance >= date.today()
            })
        
        # Convertir les montants en float pour la sérialisation JSON
        for account_data in accounts_data.values():
            account_data['total_montant'] = float(account_data['total_montant'])
        
        return Response(list(accounts_data.values()))
    
    @action(detail=True, methods=['post'])
    def extend(self, request, pk=None):
        """Prolonger l'échéance d'un prélèvement"""
        direct_debit = self.get_object()
        new_echeance = request.data.get('echeance')
        
        if not new_echeance:
            return Response(
                {'error': 'La nouvelle échéance est requise'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            new_echeance = datetime.strptime(new_echeance, '%Y-%m-%d').date()
            
            if new_echeance < date.today():
                return Response(
                    {'error': 'La nouvelle échéance ne peut pas être dans le passé'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            direct_debit.echeance = new_echeance
            direct_debit.save()
            
            serializer = DirectDebitSerializer(direct_debit)
            return Response({
                'message': 'Échéance prolongée avec succès',
                'prélèvement': serializer.data
            })
            
        except (ValueError, TypeError):
            return Response(
                {'error': 'Format de date invalide. Utilisez YYYY-MM-DD'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def bulk_update_status(self, request):
        """Mettre à jour le statut de plusieurs prélèvements"""
        debit_ids = request.data.get('debit_ids', [])
        action_type = request.data.get('action')  # 'activate', 'deactivate', 'extend'
        new_echeance = request.data.get('echeance')
        
        if not debit_ids:
            return Response(
                {'error': 'Aucun prélèvement spécifié'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        direct_debits = self.get_queryset().filter(id__in=debit_ids)
        updated_count = 0
        errors = []
        
        for debit in direct_debits:
            try:
                if action_type == 'activate':
                    debit.echeance = None  # Activer (pas d'échéance)
                elif action_type == 'deactivate':
                    debit.echeance = date.today() - timedelta(days=1)  # Désactiver
                elif action_type == 'extend' and new_echeance:
                    new_echeance_date = datetime.strptime(new_echeance, '%Y-%m-%d').date()
                    if new_echeance_date >= date.today():
                        debit.echeance = new_echeance_date
                    else:
                        errors.append(f"Échéance invalide pour le prélèvement {debit.id}")
                        continue
                
                debit.save()
                updated_count += 1
                
            except Exception as e:
                errors.append(f"Erreur lors de la mise à jour du prélèvement {debit.id}: {str(e)}")
        
        return Response({
            'updated_count': updated_count,
            'error_count': len(errors),
            'errors': errors
        })
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Résumé des prélèvements automatiques"""
        direct_debits = self.get_queryset()
        today = date.today()
        
        # Compter par statut
        active = direct_debits.filter(Q(echeance__isnull=True) | Q(echeance__gte=today)).count()
        expired = direct_debits.filter(echeance__lt=today).count()
        
        # Montants totaux
        total_montant = direct_debits.aggregate(total=Sum('montant'))['total'] or Decimal('0.00')
        active_montant = direct_debits.filter(
            Q(echeance__isnull=True) | Q(echeance__gte=today)
        ).aggregate(total=Sum('montant'))['total'] or Decimal('0.00')
        
        return Response({
            'total_prélèvements': direct_debits.count(),
            'prélèvements_actifs': active,
            'prélèvements_expirés': expired,
            'total_montant': float(total_montant),
            'montant_actifs': float(active_montant)
        }) 