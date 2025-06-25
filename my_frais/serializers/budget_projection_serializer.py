from rest_framework import serializers
from my_frais.models import BudgetProjection, Account, DirectDebit, RecurringIncome
from decimal import Decimal
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta


class BudgetProjectionSerializer(serializers.ModelSerializer):
    compte_reference_username = serializers.CharField(source='compte_reference.user.username', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = BudgetProjection
        fields = [
            'id', 'compte_reference', 'compte_reference_username',
            'date_projection', 'periode_projection', 'solde_initial',
            'projections_data', 'created_by', 'created_by_username',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'solde_initial', 'projections_data', 'created_by', 'created_by_username', 'created_at', 'updated_at']
    
    def validate_periode_projection(self, value):
        """Validation de la période de projection"""
        if value <= 0:
            raise serializers.ValidationError("La période de projection doit être positive.")
        if value > 60:  # Limite à 5 ans
            raise serializers.ValidationError("La période de projection ne peut pas dépasser 60 mois.")
        return value
    
    def validate_compte_reference(self, value):
        """Validation du compte de référence"""
        if not Account.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Le compte de référence spécifié n'existe pas.")
        return value
    
    def create(self, validated_data):
        """Création d'une projection de budget avec calcul automatique"""
        validated_data['created_by'] = self.context['request'].user
        validated_data['solde_initial'] = validated_data['compte_reference'].solde
        
        # Utiliser le calculateur pour générer les projections
        calculator = BudgetProjectionCalculatorSerializer(context=self.context)
        projections_data = calculator.calculate_projections(
            compte=validated_data['compte_reference'],
            date_debut=validated_data['date_projection'],
            periode_mois=validated_data['periode_projection'],
            inclure_prelevements=True,
            inclure_revenus=True
        )
        validated_data['projections_data'] = projections_data
        
        return super().create(validated_data)


class BudgetProjectionCalculatorSerializer(serializers.Serializer):
    """Serializer pour calculer les projections de budget sans les sauvegarder"""
    compte_reference = serializers.PrimaryKeyRelatedField(queryset=Account.objects.all())
    date_debut = serializers.DateField(default=date.today)
    periode_mois = serializers.IntegerField(min_value=1, max_value=60, default=12)
    inclure_prelevements = serializers.BooleanField(default=True)
    inclure_revenus = serializers.BooleanField(default=True)
    
    def validate_compte_reference(self, value):
        """Validation du compte de référence selon l'utilisateur connecté"""
        user = self.context['request'].user
        if not user.is_staff and value.user != user:
            raise serializers.ValidationError("Vous ne pouvez pas accéder à ce compte.")
        return value
    
    def calculate_projections(self, compte, date_debut, periode_mois, inclure_prelevements=True, inclure_revenus=True):
        """
        Calcule les projections de budget en prenant en compte :
        - Les prélèvements récurrents
        - Les revenus récurrents
        - Les opérations ponctuelles déjà programmées
        """
        date_fin = date_debut + relativedelta(months=periode_mois)
        projections = []
        solde_courant = compte.solde
        
        # Collecter toutes les transactions futures
        transactions_futures = []
        
        # Ajouter les prélèvements récurrents si demandé
        if inclure_prelevements:
            prelevements = DirectDebit.objects.filter(
                compte_reference=compte,
                actif=True,
                date_prelevement__lte=date_fin
            )
            
            for prelevement in prelevements:
                occurrences = prelevement.get_occurrences_until(date_fin)
                transactions_futures.extend(occurrences)
        
        # Ajouter les revenus récurrents si demandé
        if inclure_revenus:
            revenus = RecurringIncome.objects.filter(
                compte_reference=compte,
                actif=True,
                date_premier_versement__lte=date_fin
            )
            
            for revenu in revenus:
                occurrences = revenu.get_occurrences_until(date_fin)
                transactions_futures.extend(occurrences)
        
        # Trier toutes les transactions par date
        transactions_futures.sort(key=lambda x: x['date'])
        
        # Générer les projections mensuelles
        date_courante = date_debut
        
        for mois in range(periode_mois):
            debut_mois = date_courante
            fin_mois = debut_mois + relativedelta(months=1) - timedelta(days=1)
            
            # Transactions du mois
            transactions_mois = [
                t for t in transactions_futures 
                if debut_mois <= t['date'] <= fin_mois
            ]
            
            # Calculer les totaux du mois
            total_revenus = sum(
                t['montant'] for t in transactions_mois 
                if t['montant'] > 0
            )
            total_prelevements = sum(
                abs(t['montant']) for t in transactions_mois 
                if t['montant'] < 0
            )
            
            solde_debut_mois = solde_courant
            solde_fin_mois = solde_courant + total_revenus - total_prelevements
            
            projection_mois = {
                'mois': mois + 1,
                'date_debut': debut_mois.isoformat(),
                'date_fin': fin_mois.isoformat(),
                'solde_debut': float(solde_debut_mois),
                'solde_fin': float(solde_fin_mois),
                'total_revenus': float(total_revenus),
                'total_prelevements': float(total_prelevements),
                'variation': float(total_revenus - total_prelevements),
                'transactions': [
                    {
                        'date': t['date'].isoformat(),
                        'montant': float(t['montant']),
                        'description': t['description'],
                        'type': t['type']
                    }
                    for t in transactions_mois
                ]
            }
            
            projections.append(projection_mois)
            solde_courant = solde_fin_mois
            date_courante = debut_mois + relativedelta(months=1)
        
        return {
            'compte_id': compte.id,
            'compte_nom': compte.nom,
            'solde_initial': float(compte.solde),
            'solde_final_projete': float(solde_courant),
            'variation_totale': float(solde_courant - compte.solde),
            'date_debut': date_debut.isoformat(),
            'date_fin': date_fin.isoformat(),
            'periode_mois': periode_mois,
            'projections_mensuelles': projections,
            'resume': {
                'revenus_totaux': float(sum(p['total_revenus'] for p in projections)),
                'prelevements_totaux': float(sum(p['total_prelevements'] for p in projections)),
                'solde_minimum': float(min(p['solde_fin'] for p in projections)),
                'solde_maximum': float(max(p['solde_fin'] for p in projections)),
                'mois_solde_negatif': len([p for p in projections if p['solde_fin'] < 0])
            }
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