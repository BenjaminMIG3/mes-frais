from rest_framework import serializers
from my_frais.models import BudgetProjection, Account, DirectDebit, RecurringIncome
from decimal import Decimal
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

from my_frais.services import BudgetProjectionService


class BudgetProjectionSerializer(serializers.ModelSerializer):
    """
    Serializer pour les projections de budget
    Utilise le nouveau système de transactions automatiques optimisé
    """
    compte_reference_nom = serializers.CharField(source='compte_reference.nom', read_only=True)
    user_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = BudgetProjection
        fields = [
            'id', 'compte_reference', 'compte_reference_nom', 'date_projection',
            'periode_projection', 'solde_initial', 'projections_data',
            'user_username', 'created_at', 'updated_at'
        ]
        read_only_fields = ['solde_initial', 'projections_data', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        """Création d'une projection de budget avec calcul automatique"""
        validated_data['created_by'] = self.context['request'].user
        validated_data['solde_initial'] = validated_data['compte_reference'].solde
        
        # Utiliser le nouveau service pour générer les projections
        projections_data = BudgetProjectionService.calculate_projections(
            compte=validated_data['compte_reference'],
            start_date=validated_data['date_projection'],
            period_months=validated_data['periode_projection'],
            include_payments=True,
            include_incomes=True
        )
        validated_data['projections_data'] = projections_data
        
        return super().create(validated_data)


class BudgetProjectionCalculatorSerializer(serializers.Serializer):
    """
    Serializer pour calculer les projections de budget
    Utilise le nouveau système de transactions automatiques
    """
    compte = serializers.PrimaryKeyRelatedField(queryset=Account.objects.all())
    date_debut = serializers.DateField()
    periode_mois = serializers.IntegerField(min_value=1, max_value=60)
    inclure_prelevements = serializers.BooleanField(default=True)
    inclure_revenus = serializers.BooleanField(default=True)
    
    def calculate_projections(self, compte, date_debut, periode_mois, inclure_prelevements=True, inclure_revenus=True):
        """
        Calcule les projections de budget en utilisant le nouveau service
        """
        return BudgetProjectionService.calculate_projections(
            account=compte,
            start_date=date_debut,
            period_months=periode_mois,
            include_payments=inclure_prelevements,
            include_incomes=inclure_revenus
        )
    
    def validate_periode_mois(self, value):
        """Validation de la période de projection"""
        if value < 1:
            raise serializers.ValidationError("La période doit être d'au moins 1 mois")
        if value > 60:
            raise serializers.ValidationError("La période ne peut pas dépasser 60 mois")
        return value
    
    def validate_date_debut(self, value):
        """Validation de la date de début"""
        if value < date.today():
            raise serializers.ValidationError("La date de début ne peut pas être dans le passé")
        return value


class BudgetProjectionDetailSerializer(serializers.ModelSerializer):
    """
    Serializer détaillé pour les projections de budget
    Inclut des informations supplémentaires sur les transactions
    """
    compte_reference_nom = serializers.CharField(source='compte_reference.nom', read_only=True)
    user_username = serializers.CharField(source='created_by.username', read_only=True)
    projections_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = BudgetProjection
        fields = [
            'id', 'compte_reference', 'compte_reference_nom', 'date_projection',
            'periode_projection', 'solde_initial', 'projections_data',
            'projections_summary', 'user_username', 'created_at', 'updated_at'
        ]
    
    def get_projections_summary(self, obj):
        """Calcule un résumé des projections"""
        if not obj.projections_data:
            return {}
        
        projections = obj.projections_data
        total_transactions = sum(p.get('transactions_count', 0) for p in projections)
        total_impact = sum(p.get('total_transactions', 0) for p in projections)
        
        # Trouver le solde final
        final_balance = projections[-1].get('solde_fin', 0) if projections else obj.solde_initial
        
        return {
            'total_transactions': total_transactions,
            'total_impact': float(total_impact),
            'solde_final': float(final_balance),
            'evolution_solde': float(final_balance - obj.solde_initial),
            'moyenne_mensuelle': float(total_impact / len(projections)) if projections else 0
        }


class BudgetSummarySerializer(serializers.Serializer):
    """Serializer pour le résumé budgétaire d'un compte"""
    
    def get_budget_summary(self, compte):
        """Génère un résumé budgétaire complet pour un compte"""
        # Prélèvements actifs
        prelevements = DirectDebit.objects.filter(
            compte_reference=compte,
            actif=True
        )
        
        # Revenus actifs
        revenus = RecurringIncome.objects.filter(
            compte_reference=compte,
            actif=True
        )
        
        # Calcul des montants mensuels équivalents
        prelevements_mensuels = Decimal('0.00')
        for prelevement in prelevements:
            if prelevement.frequence == 'Mensuel':
                prelevements_mensuels += prelevement.montant
            elif prelevement.frequence == 'Trimestriel':
                prelevements_mensuels += prelevement.montant / Decimal('3')
            elif prelevement.frequence == 'Annuel':
                prelevements_mensuels += prelevement.montant / Decimal('12')
        
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
        
        return {
            'compte': {
                'id': compte.id,
                'nom': compte.nom,
                'solde_actuel': float(compte.solde)
            },
            'prelevements': {
                'count': prelevements.count(),
                'montant_mensuel': float(prelevements_mensuels),
                'details': [
                    {
                        'description': p.description,
                        'montant': float(p.montant),
                        'frequence': p.frequence,
                        'prochaine_occurrence': p.get_next_occurrence().isoformat() if p.get_next_occurrence() else None
                    }
                    for p in prelevements
                ]
            },
            'revenus': {
                'count': revenus.count(),
                'montant_mensuel': float(revenus_mensuels),
                'details': [
                    {
                        'description': r.description,
                        'type': r.type_revenu,
                        'montant': float(r.montant),
                        'frequence': r.frequence,
                        'prochaine_occurrence': r.get_next_occurrence().isoformat() if r.get_next_occurrence() else None
                    }
                    for r in revenus
                ]
            },
            'projection_mensuelle': {
                'revenus': float(revenus_mensuels),
                'prelevements': float(prelevements_mensuels),
                'solde_estime': float(solde_mensuel_estime),
                'status': 'positif' if solde_mensuel_estime > 0 else 'negatif'
            }
        } 