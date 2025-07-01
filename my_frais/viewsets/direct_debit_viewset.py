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
        """Filtrer les prélèvements selon l'utilisateur connecté avec optimisation"""
        user = self.request.user
        if user.is_staff:
            return DirectDebit.objects.select_related('compte_reference', 'compte_reference__user', 'created_by').all()
        return DirectDebit.objects.select_related('compte_reference', 'compte_reference__user', 'created_by').filter(compte_reference__user=user)
    
    def get_serializer_class(self):
        """Utiliser le serializer approprié selon l'action"""
        if self.action == 'list':
            return DirectDebitListSerializer
        elif self.action == 'summary':
            return DirectDebitSummarySerializer
        return DirectDebitSerializer
    
    def create(self, request, *args, **kwargs):
        """Créer un prélèvement automatique avec debug des erreurs 400"""
        print(f"🔵 POST /direct-debits/ - Données reçues:")
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
        print(f"✅ SUCCÈS - DirectDebit créé: ID {serializer.data.get('id')}")
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
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
        total_montant = active_debits.aggregate(total=Sum('montant'))['total'] or Decimal('0.00')
        
        return Response({
            'count': active_debits.count(),
            'prélèvements': serializer.data,
            'total_montant': float(total_montant)
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
            'count': expired_debits.count(),
            'prélèvements': serializer.data
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
        
        # Prochain prélèvement
        prochain_prelevement = upcoming_debits.first()
        
        return Response({
            'count': upcoming_debits.count(),
            'prélèvements': serializer.data,
            'prochain_prélèvement': prochain_prelevement.date_prelevement.isoformat() if prochain_prelevement else None
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
                'prélèvements_actifs': active_count,
                'prélèvements_expirés': expired_count,
                'total_montant_actif': float(active_montant),
                'prélèvements_ce_mois': this_month_count,
                'montant_ce_mois': float(this_month_montant)
            }
        })
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Tableau de bord des prélèvements automatiques"""
        direct_debits = self.get_queryset()
        today = date.today()
        
        # Résumé général
        total_debits = direct_debits.count()
        active_debits = direct_debits.filter(
            Q(echeance__isnull=True) | Q(echeance__gte=today)
        )
        active_count = active_debits.count()
        total_montant = active_debits.aggregate(total=Sum('montant'))['total'] or Decimal('0.00')
        
        # Prélèvements à venir (7 jours)
        seven_days_later = today + timedelta(days=7)
        upcoming_7_days = direct_debits.filter(
            date_prelevement__gte=today,
            date_prelevement__lte=seven_days_later
        )
        upcoming_7_count = upcoming_7_days.count()
        upcoming_7_montant = upcoming_7_days.aggregate(total=Sum('montant'))['total'] or Decimal('0.00')
        
        # Répartition par fréquence
        by_frequency = {}
        for debit in active_debits:
            freq = debit.frequence
            if freq not in by_frequency:
                by_frequency[freq] = 0
            by_frequency[freq] += 1
        
        # Prochain prélèvement
        prochain_prelevement = direct_debits.filter(
            date_prelevement__gte=today
        ).order_by('date_prelevement').first()
        
        return Response({
            'summary': {
                'total_prélèvements': total_debits,
                'prélèvements_actifs': active_count,
                'total_montant': float(total_montant)
            },
            'upcoming': {
                'prochain_prélèvement': prochain_prelevement.date_prelevement.isoformat() if prochain_prelevement else None,
                'prélèvements_7_jours': upcoming_7_count,
                'montant_7_jours': float(upcoming_7_montant)
            },
            'by_frequency': by_frequency
        })
    
    @action(detail=True, methods=['post'])
    def extend(self, request, pk=None):
        """Prolonger l'échéance d'un prélèvement"""
        debit = self.get_object()
        nouvelle_echeance = request.data.get('nouvelle_echeance')
        
        if not nouvelle_echeance:
            return Response(
                {'error': 'La nouvelle échéance est requise'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            nouvelle_date = datetime.strptime(nouvelle_echeance, '%Y-%m-%d').date()
            debit.echeance = nouvelle_date
            debit.save()
            
            return Response({
                'message': 'Échéance prolongée avec succès',
                'nouvelle_echeance': nouvelle_echeance
            })
            
        except ValueError:
            return Response(
                {'error': 'Format de date invalide. Utilisez YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def bulk_status(self, request):
        """Mettre à jour le statut de plusieurs prélèvements"""
        prelevements_ids = request.data.get('prélèvements_ids', [])
        actif = request.data.get('actif')
        
        if actif is None:
            return Response(
                {'error': 'Le statut actif est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not prelevements_ids:
            return Response(
                {'error': 'Aucun prélèvement spécifié'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Vérifier les permissions
        user = request.user
        if not user.is_staff:
            # Vérifier que tous les prélèvements appartiennent à l'utilisateur
            user_debits = DirectDebit.objects.filter(
                id__in=prelevements_ids,
                compte_reference__user=user
            )
            if user_debits.count() != len(prelevements_ids):
                return Response(
                    {'error': 'Vous ne pouvez pas modifier certains prélèvements'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Mettre à jour le statut
        updated_count = DirectDebit.objects.filter(id__in=prelevements_ids).update(actif=actif)
        
        return Response({
            'message': f'{updated_count} prélèvement(s) mis à jour',
            'updated_count': updated_count,
            'actif': actif
        })
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Résumé des prélèvements automatiques"""
        direct_debits = self.get_queryset()
        today = date.today()
        
        # Statistiques par compte
        accounts_summary = {}
        for debit in direct_debits:
            account_id = debit.compte_reference.id
            account_name = debit.compte_reference.nom
            
            if account_id not in accounts_summary:
                accounts_summary[account_id] = {
                    'account_id': account_id,
                    'account_name': account_name,
                    'total_prélèvements': 0,
                    'prélèvements_actifs': 0,
                    'total_montant': Decimal('0.00')
                }
            
            accounts_summary[account_id]['total_prélèvements'] += 1
            accounts_summary[account_id]['total_montant'] += debit.montant
            
            if debit.actif and (not debit.echeance or debit.echeance >= today):
                accounts_summary[account_id]['prélèvements_actifs'] += 1
        
        # Convertir les montants en float
        for summary in accounts_summary.values():
            summary['total_montant'] = float(summary['total_montant'])
        
        return Response({
            'accounts_summary': list(accounts_summary.values()),
            'total_accounts': len(accounts_summary)
        }) 