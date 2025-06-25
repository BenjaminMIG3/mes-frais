from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from datetime import date, timedelta
from decimal import Decimal

from my_frais.models import BudgetProjection, Account, DirectDebit, RecurringIncome
from my_frais.serializers.budget_projection_serializer import (
    BudgetProjectionSerializer, BudgetProjectionCalculatorSerializer, BudgetSummarySerializer
)


class BudgetProjectionViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des projections de budget.
    
    Permet de créer, lire, mettre à jour et supprimer des projections de budget.
    Inclut des actions personnalisées pour le calcul en temps réel et les résumés.
    """
    queryset = BudgetProjection.objects.all()
    serializer_class = BudgetProjectionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['compte_reference', 'periode_projection']
    search_fields = ['compte_reference__nom', 'compte_reference__user__username']
    ordering_fields = ['date_projection', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filtrer les projections selon l'utilisateur connecté"""
        user = self.request.user
        if user.is_staff:
            return BudgetProjection.objects.all()
        return BudgetProjection.objects.filter(compte_reference__user=user)
    
    def perform_create(self, serializer):
        """Créer une projection avec l'utilisateur connecté comme créateur"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['post'])
    def calculate(self, request):
        """Calculer les projections de budget en temps réel sans les sauvegarder"""
        serializer = BudgetProjectionCalculatorSerializer(data=request.data, context={'request': request})
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        validated_data = serializer.validated_data
        projections = serializer.calculate_projections(
            compte=validated_data['compte_reference'],
            date_debut=validated_data['date_debut'],
            periode_mois=validated_data['periode_mois'],
            inclure_prelevements=validated_data['inclure_prelevements'],
            inclure_revenus=validated_data['inclure_revenus']
        )
        
        return Response(projections)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Obtenir un résumé budgétaire pour un ou tous les comptes"""
        compte_id = request.query_params.get('compte_id')
        
        if compte_id:
            try:
                compte = Account.objects.get(id=compte_id)
                # Vérifier les permissions
                if not request.user.is_staff and compte.user != request.user:
                    return Response(
                        {'error': 'Vous ne pouvez pas accéder à ce compte'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                
                summary_serializer = BudgetSummarySerializer()
                summary = summary_serializer.get_budget_summary(compte)
                return Response(summary)
            
            except Account.DoesNotExist:
                return Response(
                    {'error': 'Compte non trouvé'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Résumé pour tous les comptes de l'utilisateur
            if request.user.is_staff:
                comptes = Account.objects.all()
            else:
                comptes = Account.objects.filter(user=request.user)
            
            summary_serializer = BudgetSummarySerializer()
            summaries = []
            
            for compte in comptes:
                summary = summary_serializer.get_budget_summary(compte)
                summaries.append(summary)
            
            return Response({
                'comptes_count': len(summaries),
                'summaries': summaries
            })
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Tableau de bord avec les indicateurs clés"""
        user = request.user
        
        if user.is_staff:
            comptes = Account.objects.all()
            prelevements = DirectDebit.objects.filter(actif=True)
            revenus = RecurringIncome.objects.filter(actif=True)
        else:
            comptes = Account.objects.filter(user=user)
            prelevements = DirectDebit.objects.filter(compte_reference__user=user, actif=True)
            revenus = RecurringIncome.objects.filter(compte_reference__user=user, actif=True)
        
        # Calculs des totaux
        solde_total = sum(compte.solde for compte in comptes)
        
        # Prélèvements mensuels équivalents
        prelevements_mensuels = Decimal('0.00')
        for prelevement in prelevements:
            if prelevement.frequence == 'Mensuel':
                prelevements_mensuels += prelevement.montant
            elif prelevement.frequence == 'Trimestriel':
                prelevements_mensuels += prelevement.montant / Decimal('3')
            elif prelevement.frequence == 'Annuel':
                prelevements_mensuels += prelevement.montant / Decimal('12')
        
        # Revenus mensuels équivalents
        revenus_mensuels = Decimal('0.00')
        for revenu in revenus:
            if revenu.frequence == 'Hebdomadaire':
                revenus_mensuels += revenu.montant * Decimal('4.33')
            elif revenu.frequence == 'Mensuel':
                revenus_mensuels += revenu.montant
            elif revenu.frequence == 'Trimestriel':
                revenus_mensuels += revenu.montant / Decimal('3')
            elif revenu.frequence == 'Annuel':
                revenus_mensuels += revenu.montant / Decimal('12')
        
        solde_mensuel_estime = revenus_mensuels - prelevements_mensuels
        
        # Prochaines échéances (30 jours)
        date_limite = date.today() + timedelta(days=30)
        
        prochains_prelevements = []
        for prelevement in prelevements:
            next_occurrence = prelevement.get_next_occurrence()
            if next_occurrence and next_occurrence <= date_limite:
                prochains_prelevements.append({
                    'id': prelevement.id,
                    'description': prelevement.description,
                    'montant': float(prelevement.montant),
                    'date': next_occurrence.isoformat(),
                    'jours_restants': (next_occurrence - date.today()).days,
                    'compte': prelevement.compte_reference.nom
                })
        
        prochains_revenus = []
        for revenu in revenus:
            next_occurrence = revenu.get_next_occurrence()
            if next_occurrence and next_occurrence <= date_limite:
                prochains_revenus.append({
                    'id': revenu.id,
                    'description': revenu.description,
                    'type': revenu.type_revenu,
                    'montant': float(revenu.montant),
                    'date': next_occurrence.isoformat(),
                    'jours_restants': (next_occurrence - date.today()).days,
                    'compte': revenu.compte_reference.nom
                })
        
        # Trier par date
        prochains_prelevements.sort(key=lambda x: x['date'])
        prochains_revenus.sort(key=lambda x: x['date'])
        
        # Comptes en déficit potentiel
        comptes_alerte = []
        for compte in comptes:
            if compte.solde < prelevements_mensuels:
                comptes_alerte.append({
                    'id': compte.id,
                    'nom': compte.nom,
                    'solde': float(compte.solde),
                    'deficit_potentiel': float(prelevements_mensuels - compte.solde)
                })
        
        return Response({
            'overview': {
                'comptes_count': comptes.count(),
                'solde_total': float(solde_total),
                'revenus_mensuels': float(revenus_mensuels),
                'prelevements_mensuels': float(prelevements_mensuels),
                'solde_mensuel_estime': float(solde_mensuel_estime),
                'status': 'positif' if solde_mensuel_estime > 0 else 'negatif'
            },
            'alertes': {
                'comptes_en_deficit': len(comptes_alerte),
                'comptes_details': comptes_alerte
            },
            'prochaines_echeances': {
                'prelevements_30j': {
                    'count': len(prochains_prelevements),
                    'montant_total': sum(p['montant'] for p in prochains_prelevements),
                    'details': prochains_prelevements[:10]  # Limiter à 10
                },
                'revenus_30j': {
                    'count': len(prochains_revenus),
                    'montant_total': sum(r['montant'] for r in prochains_revenus),
                    'details': prochains_revenus[:10]  # Limiter à 10
                }
            }
        })
    
    @action(detail=False, methods=['post'])
    def quick_projection(self, request):
        """Projection rapide pour les 6 prochains mois"""
        compte_id = request.data.get('compte_id')
        
        if not compte_id:
            return Response(
                {'error': 'ID du compte requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            compte = Account.objects.get(id=compte_id)
            # Vérifier les permissions
            if not request.user.is_staff and compte.user != request.user:
                return Response(
                    {'error': 'Vous ne pouvez pas accéder à ce compte'},
                    status=status.HTTP_403_FORBIDDEN
                )
        except Account.DoesNotExist:
            return Response(
                {'error': 'Compte non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Calculer la projection rapide
        calculator = BudgetProjectionCalculatorSerializer(context={'request': request})
        projections = calculator.calculate_projections(
            compte=compte,
            date_debut=date.today(),
            periode_mois=6,
            inclure_prelevements=True,
            inclure_revenus=True
        )
        
        # Extraire les informations clés
        quick_data = {
            'compte': {
                'id': compte.id,
                'nom': compte.nom,
                'solde_actuel': float(compte.solde)
            },
            'projection_6_mois': {
                'solde_final': projections['solde_final_projete'],
                'variation_totale': projections['variation_totale'],
                'revenus_totaux': projections['resume']['revenus_totaux'],
                'prelevements_totaux': projections['resume']['prelevements_totaux'],
                'solde_minimum': projections['resume']['solde_minimum'],
                'mois_solde_negatif': projections['resume']['mois_solde_negatif']
            },
            'alertes': {
                'deficit_prevu': projections['resume']['solde_minimum'] < 0,
                'amelioration': projections['variation_totale'] > 0
            }
        }
        
        return Response(quick_data)
    
    @action(detail=False, methods=['get'])
    def compare_scenarios(self, request):
        """Comparer différents scénarios de projection"""
        compte_id = request.query_params.get('compte_id')
        
        if not compte_id:
            return Response(
                {'error': 'ID du compte requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            compte = Account.objects.get(id=compte_id)
            # Vérifier les permissions
            if not request.user.is_staff and compte.user != request.user:
                return Response(
                    {'error': 'Vous ne pouvez pas accéder à ce compte'},
                    status=status.HTTP_403_FORBIDDEN
                )
        except Account.DoesNotExist:
            return Response(
                {'error': 'Compte non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        calculator = BudgetProjectionCalculatorSerializer(context={'request': request})
        
        # Scénario 1: Avec tout (baseline)
        scenario_complet = calculator.calculate_projections(
            compte=compte, date_debut=date.today(), periode_mois=12,
            inclure_prelevements=True, inclure_revenus=True
        )
        
        # Scénario 2: Uniquement les prélèvements
        scenario_prelevements = calculator.calculate_projections(
            compte=compte, date_debut=date.today(), periode_mois=12,
            inclure_prelevements=True, inclure_revenus=False
        )
        
        # Scénario 3: Uniquement les revenus
        scenario_revenus = calculator.calculate_projections(
            compte=compte, date_debut=date.today(), periode_mois=12,
            inclure_prelevements=False, inclure_revenus=True
        )
        
        return Response({
            'compte': {
                'id': compte.id,
                'nom': compte.nom,
                'solde_actuel': float(compte.solde)
            },
            'scenarios': {
                'complet': {
                    'nom': 'Projection complète',
                    'solde_final': scenario_complet['solde_final_projete'],
                    'variation': scenario_complet['variation_totale'],
                    'solde_minimum': scenario_complet['resume']['solde_minimum'],
                    'mois_deficit': scenario_complet['resume']['mois_solde_negatif']
                },
                'prelevements_seulement': {
                    'nom': 'Prélèvements uniquement',
                    'solde_final': scenario_prelevements['solde_final_projete'],
                    'variation': scenario_prelevements['variation_totale'],
                    'solde_minimum': scenario_prelevements['resume']['solde_minimum'],
                    'mois_deficit': scenario_prelevements['resume']['mois_solde_negatif']
                },
                'revenus_seulement': {
                    'nom': 'Revenus uniquement',
                    'solde_final': scenario_revenus['solde_final_projete'],
                    'variation': scenario_revenus['variation_totale'],
                    'solde_minimum': scenario_revenus['resume']['solde_minimum'],
                    'mois_deficit': scenario_revenus['resume']['mois_solde_negatif']
                }
            }
        }) 