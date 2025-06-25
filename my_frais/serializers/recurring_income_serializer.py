from rest_framework import serializers
from my_frais.models import RecurringIncome, Account
from decimal import Decimal
from datetime import date


class RecurringIncomeSerializer(serializers.ModelSerializer):
    compte_reference_username = serializers.CharField(source='compte_reference.user.username', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    is_active = serializers.SerializerMethodField()
    next_occurrence = serializers.SerializerMethodField()
    
    class Meta:
        model = RecurringIncome
        fields = [
            'id', 'compte_reference', 'compte_reference_username',
            'montant', 'description', 'date_premier_versement', 'date_fin',
            'frequence', 'actif', 'type_revenu', 'created_by', 'created_by_username',
            'created_at', 'updated_at', 'is_active', 'next_occurrence'
        ]
        read_only_fields = ['id', 'created_by', 'created_by_username', 'created_at', 'updated_at']
    
    def get_is_active(self, obj):
        """Déterminer si le revenu récurrent est actif"""
        if not obj.actif:
            return False
        if obj.date_fin:
            return obj.date_fin >= date.today()
        return True
    
    def get_next_occurrence(self, obj):
        """Obtenir la prochaine occurrence du revenu"""
        next_date = obj.get_next_occurrence()
        return next_date.isoformat() if next_date else None
    
    def validate_montant(self, value):
        """Validation du montant - doit être positif pour les revenus"""
        if value <= Decimal('0.00'):
            raise serializers.ValidationError("Le montant du revenu doit être positif.")
        return value
    
    def validate_compte_reference(self, value):
        """Validation du compte de référence"""
        if not Account.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Le compte de référence spécifié n'existe pas.")
        return value
    
    def validate_description(self, value):
        """Validation de la description"""
        if len(value.strip()) == 0:
            raise serializers.ValidationError("La description ne peut pas être vide.")
        if len(value) > 255:
            raise serializers.ValidationError("La description ne peut pas dépasser 255 caractères.")
        return value.strip()
    
    def validate_date_premier_versement(self, value):
        """Validation de la date du premier versement"""
        if value < date.today():
            raise serializers.ValidationError("La date du premier versement ne peut pas être dans le passé.")
        return value
    
    def validate_date_fin(self, value):
        """Validation de la date de fin"""
        if value and value < date.today():
            raise serializers.ValidationError("La date de fin ne peut pas être dans le passé.")
        return value
    
    def validate(self, data):
        """Validation croisée des dates"""
        date_premier_versement = data.get('date_premier_versement')
        date_fin = data.get('date_fin')
        
        if date_fin and date_premier_versement and date_fin < date_premier_versement:
            raise serializers.ValidationError("La date de fin ne peut pas être antérieure à la date du premier versement.")
        
        return data
    
    def create(self, validated_data):
        """Création d'un revenu récurrent"""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Mise à jour d'un revenu récurrent"""
        # Empêcher la modification du compte de référence
        if 'compte_reference' in validated_data:
            del validated_data['compte_reference']
        return super().update(instance, validated_data)


class RecurringIncomeListSerializer(serializers.ModelSerializer):
    """Serializer pour la liste des revenus récurrents"""
    compte_reference_username = serializers.CharField(source='compte_reference.user.username', read_only=True)
    is_active = serializers.SerializerMethodField()
    next_occurrence = serializers.SerializerMethodField()
    
    class Meta:
        model = RecurringIncome
        fields = ['id', 'compte_reference_username', 'montant', 'description', 
                 'date_premier_versement', 'date_fin', 'frequence', 'type_revenu',
                 'is_active', 'next_occurrence', 'created_at']
    
    def get_is_active(self, obj):
        """Déterminer si le revenu récurrent est actif"""
        if not obj.actif:
            return False
        if obj.date_fin:
            return obj.date_fin >= date.today()
        return True
    
    def get_next_occurrence(self, obj):
        """Obtenir la prochaine occurrence du revenu"""
        next_date = obj.get_next_occurrence()
        return next_date.isoformat() if next_date else None


class RecurringIncomeSummarySerializer(serializers.ModelSerializer):
    """Serializer pour le résumé des revenus récurrents"""
    compte_reference_username = serializers.CharField(source='compte_reference.user.username', read_only=True)
    status = serializers.SerializerMethodField()
    montant_mensuel_equivalent = serializers.SerializerMethodField()
    
    class Meta:
        model = RecurringIncome
        fields = ['id', 'compte_reference_username', 'montant', 'description', 
                 'type_revenu', 'frequence', 'status', 'montant_mensuel_equivalent']
    
    def get_status(self, obj):
        """Obtenir le statut du revenu récurrent"""
        if not obj.actif:
            return "inactif"
        elif obj.date_fin and obj.date_fin < date.today():
            return "expiré"
        elif obj.date_premier_versement <= date.today():
            return "actif"
        else:
            return "programmé"
    
    def get_montant_mensuel_equivalent(self, obj):
        """Calculer le montant mensuel équivalent selon la fréquence"""
        if obj.frequence == 'Hebdomadaire':
            return float(obj.montant * Decimal('4.33'))  # 52 semaines / 12 mois
        elif obj.frequence == 'Mensuel':
            return float(obj.montant)
        elif obj.frequence == 'Trimestriel':
            return float(obj.montant / Decimal('3'))
        elif obj.frequence == 'Annuel':
            return float(obj.montant / Decimal('12'))
        return float(obj.montant) 