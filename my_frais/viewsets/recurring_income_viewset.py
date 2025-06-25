from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Count, Q
from datetime import datetime, timedelta, date
from decimal import Decimal

from my_frais.models import RecurringIncome, Account
from my_frais.serializers.recurring_income_serializer import (
    RecurringIncomeSerializer, RecurringIncomeListSerializer, RecurringIncomeSummarySerializer
)


class RecurringIncomeViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des revenus récurrents.
    
    Permet de créer, lire, mettre à jour et supprimer des revenus récurrents.
    Inclut des actions personnalisées pour les statistiques et la recherche.
    """
    queryset = RecurringIncome.objects.all()
    serializer_class = RecurringIncomeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['compte_reference', 'type_revenu', 'frequence', 'actif']
    search_fields = ['description', 'type_revenu']
    ordering_fields = ['montant', 'date_premier_versement', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filtrer les revenus récurrents selon l'utilisateur connecté"""
        user = self.request.user
        if user.is_staff:
            return RecurringIncome.objects.all()
        return RecurringIncome.objects.filter(compte_reference__user=user)
    
    def get_serializer_class(self):
        """Utiliser le serializer approprié selon l'action"""
        if self.action == 'list':
            return RecurringIncomeListSerializer
        elif self.action == 'summary':
            return RecurringIncomeSummarySerializer
        return RecurringIncomeSerializer
    
    def perform_create(self, serializer):
        """Créer un revenu récurrent avec l'utilisateur connecté comme créateur"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Obtenir les statistiques des revenus récurrents"""
        revenus = self.get_queryset()
        
        # Statistiques générales
        total_revenus = revenus.count()
        revenus_actifs = revenus.filter(actif=True).count()
        
        # Calcul du montant mensuel total équivalent
        montant_mensuel_total = Decimal('0.00')
        for revenu in revenus.filter(actif=True):
            if revenu.frequence == 'Hebdomadaire':
                montant_mensuel_total += revenu.montant * Decimal('4.33')
            elif revenu.frequence == 'Mensuel':
                montant_mensuel_total += revenu.montant
            elif revenu.frequence == 'Trimestriel':
                montant_mensuel_total += revenu.montant / Decimal('3')
            elif revenu.frequence == 'Annuel':
                montant_mensuel_total += revenu.montant / Decimal('12')
        
        # Statistiques par type de revenu
        stats_par_type = {}
        for type_revenu in ['Salaire', 'Subvention', 'Aide', 'Pension', 'Loyer', 'Autre']:
            revenus_type = revenus.filter(type_revenu=type_revenu, actif=True)
            montant_type = sum(r.montant for r in revenus_type)
            stats_par_type[type_revenu] = {
                'count': revenus_type.count(),
                'montant_total': float(montant_type)
            }
        
        # Statistiques par fréquence
        stats_par_frequence = {}
        for frequence in ['Hebdomadaire', 'Mensuel', 'Trimestriel', 'Annuel']:
            revenus_freq = revenus.filter(frequence=frequence, actif=True)
            stats_par_frequence[frequence] = revenus_freq.count()
        
        return Response({
            'statistics': {
                'total_revenus': total_revenus,
                'revenus_actifs': revenus_actifs,
                'montant_mensuel_equivalent': float(montant_mensuel_total),
                'montant_annuel_equivalent': float(montant_mensuel_total * 12),
                'par_type': stats_par_type,
                'par_frequence': stats_par_frequence
            }
        })
    
    @action(detail=False, methods=['get'])
    def by_account(self, request):
        """Obtenir les revenus récurrents groupés par compte"""
        revenus = self.get_queryset()
        
        # Grouper par compte
        accounts_data = {}
        for revenu in revenus:
            account_id = revenu.compte_reference.id
            account_username = revenu.compte_reference.user.username
            
            if account_id not in accounts_data:
                accounts_data[account_id] = {
                    'account_id': account_id,
                    'account_username': account_username,
                    'revenus_count': 0,
                    'montant_mensuel_equivalent': Decimal('0.00'),
                    'revenus': []
                }
            
            # Calculer le montant mensuel équivalent
            montant_mensuel = revenu.montant
            if revenu.frequence == 'Hebdomadaire':
                montant_mensuel = revenu.montant * Decimal('4.33')
            elif revenu.frequence == 'Trimestriel':
                montant_mensuel = revenu.montant / Decimal('3')
            elif revenu.frequence == 'Annuel':
                montant_mensuel = revenu.montant / Decimal('12')
            
            accounts_data[account_id]['revenus_count'] += 1
            accounts_data[account_id]['montant_mensuel_equivalent'] += montant_mensuel
            accounts_data[account_id]['revenus'].append({
                'id': revenu.id,
                'montant': float(revenu.montant),
                'description': revenu.description,
                'type_revenu': revenu.type_revenu,
                'frequence': revenu.frequence,
                'actif': revenu.actif,
                'montant_mensuel_equivalent': float(montant_mensuel)
            })
        
        # Convertir les montants en float pour la sérialisation JSON
        for account_data in accounts_data.values():
            account_data['montant_mensuel_equivalent'] = float(account_data['montant_mensuel_equivalent'])
        
        return Response(list(accounts_data.values()))
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Obtenir uniquement les revenus récurrents actifs"""
        revenus_actifs = self.get_queryset().filter(actif=True)
        
        # Filtrer ceux qui ne sont pas expirés
        revenus_valides = []
        for revenu in revenus_actifs:
            if not revenu.date_fin or revenu.date_fin >= date.today():
                revenus_valides.append(revenu)
        
        serializer = RecurringIncomeListSerializer(revenus_valides, many=True)
        return Response({
            'count': len(revenus_valides),
            'revenus': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Obtenir les prochaines occurrences de revenus récurrents"""
        days = int(request.query_params.get('days', 30))
        date_limite = date.today() + timedelta(days=days)
        
        revenus = self.get_queryset().filter(actif=True)
        upcoming_revenus = []
        
        for revenu in revenus:
            if revenu.date_fin and revenu.date_fin < date.today():
                continue
            
            next_occurrence = revenu.get_next_occurrence()
            if next_occurrence and next_occurrence <= date_limite:
                upcoming_revenus.append({
                    'id': revenu.id,
                    'description': revenu.description,
                    'type_revenu': revenu.type_revenu,
                    'montant': float(revenu.montant),
                    'date_occurrence': next_occurrence.isoformat(),
                    'jours_restants': (next_occurrence - date.today()).days,
                    'compte': revenu.compte_reference.nom
                })
        
        # Trier par date d'occurrence
        upcoming_revenus.sort(key=lambda x: x['date_occurrence'])
        
        return Response({
            'periode': f"{days} jours",
            'count': len(upcoming_revenus),
            'revenus': upcoming_revenus
        })
    
    @action(detail=False, methods=['get'])
    def projections(self, request):
        """Calculer les projections de revenus pour une période donnée"""
        mois = int(request.query_params.get('mois', 12))
        compte_id = request.query_params.get('compte_id')
        
        revenus = self.get_queryset().filter(actif=True)
        if compte_id:
            revenus = revenus.filter(compte_reference_id=compte_id)
        
        date_fin = date.today() + timedelta(days=30 * mois)
        projections = []
        total_projete = Decimal('0.00')
        
        for revenu in revenus:
            occurrences = revenu.get_occurrences_until(date_fin)
            montant_total = sum(o['montant'] for o in occurrences)
            total_projete += montant_total
            
            projections.append({
                'revenu_id': revenu.id,
                'description': revenu.description,
                'type_revenu': revenu.type_revenu,
                'montant_unitaire': float(revenu.montant),
                'frequence': revenu.frequence,
                'occurrences_prevues': len(occurrences),
                'montant_total_projete': float(montant_total),
                'prochaines_occurrences': [
                    {
                        'date': o['date'].isoformat(),
                        'montant': o['montant']
                    }
                    for o in occurrences[:5]  # Limiter à 5 prochaines
                ]
            })
        
        return Response({
            'periode_mois': mois,
            'total_projete': float(total_projete),
            'revenus': projections
        })
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Activer/désactiver un revenu récurrent"""
        revenu = self.get_object()
        revenu.actif = not revenu.actif
        revenu.save()
        
        serializer = self.get_serializer(revenu)
        return Response({
            'message': f'Revenu {"activé" if revenu.actif else "désactivé"}',
            'revenu': serializer.data
        })
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Créer plusieurs revenus récurrents en une seule requête"""
        revenus_data = request.data.get('revenus', [])
        
        if not revenus_data:
            return Response(
                {'error': 'Aucun revenu fourni'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        created_revenus = []
        errors = []
        
        for index, revenu_data in enumerate(revenus_data):
            serializer = RecurringIncomeSerializer(data=revenu_data, context={'request': request})
            if serializer.is_valid():
                revenu = serializer.save()
                created_revenus.append(serializer.data)
            else:
                errors.append({
                    'index': index,
                    'errors': serializer.errors
                })
        
        return Response({
            'created_count': len(created_revenus),
            'created_revenus': created_revenus,
            'errors_count': len(errors),
            'errors': errors
        }, status=status.HTTP_201_CREATED if created_revenus else status.HTTP_400_BAD_REQUEST) 