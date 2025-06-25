from rest_framework import serializers
from my_frais.models import DirectDebit, Account
from decimal import Decimal
from datetime import date


class DirectDebitSerializer(serializers.ModelSerializer):
    compte_reference_username = serializers.CharField(source='compte_reference.user.username', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    is_active = serializers.SerializerMethodField()
    
    class Meta:
        model = DirectDebit
        fields = [
            'id', 'compte_reference', 'compte_reference_username',
            'montant', 'description', 'date_prelevement', 'echeance',
            'created_by', 'created_by_username', 'created_at', 'updated_at',
            'is_active'
        ]
        read_only_fields = ['id', 'created_by', 'created_by_username', 'created_at', 'updated_at']
    
    def get_is_active(self, obj):
        """Déterminer si le prélèvement est actif"""
        if obj.echeance:
            return obj.echeance >= date.today()
        return True
    
    def validate_montant(self, value):
        """Validation du montant - doit être positif pour les prélèvements"""
        if value <= Decimal('0.00'):
            raise serializers.ValidationError("Le montant du prélèvement doit être positif.")
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
    
    def validate_date_prelevement(self, value):
        """Validation de la date de prélèvement"""
        if value < date.today():
            raise serializers.ValidationError("La date de prélèvement ne peut pas être dans le passé.")
        return value
    
    def validate_echeance(self, value):
        """Validation de l'échéance"""
        if value and value < date.today():
            raise serializers.ValidationError("L'échéance ne peut pas être dans le passé.")
        return value
    
    def validate(self, data):
        """Validation croisée des dates"""
        date_prelevement = data.get('date_prelevement')
        echeance = data.get('echeance')
        
        if echeance and date_prelevement and echeance < date_prelevement:
            raise serializers.ValidationError("L'échéance ne peut pas être antérieure à la date de prélèvement.")
        
        return data
    
    def create(self, validated_data):
        """Création d'un prélèvement automatique"""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Mise à jour d'un prélèvement automatique"""
        # Empêcher la modification du compte de référence
        if 'compte_reference' in validated_data:
            del validated_data['compte_reference']
        return super().update(instance, validated_data)


class DirectDebitListSerializer(serializers.ModelSerializer):
    """Serializer pour la liste des prélèvements automatiques"""
    compte_reference_username = serializers.CharField(source='compte_reference.user.username', read_only=True)
    is_active = serializers.SerializerMethodField()
    
    class Meta:
        model = DirectDebit
        fields = ['id', 'compte_reference_username', 'montant', 'description', 
                 'date_prelevement', 'echeance', 'is_active', 'created_at']
    
    def get_is_active(self, obj):
        """Déterminer si le prélèvement est actif"""
        if obj.echeance:
            return obj.echeance >= date.today()
        return True


class DirectDebitSummarySerializer(serializers.ModelSerializer):
    """Serializer pour le résumé des prélèvements automatiques"""
    compte_reference_username = serializers.CharField(source='compte_reference.user.username', read_only=True)
    status = serializers.SerializerMethodField()
    
    class Meta:
        model = DirectDebit
        fields = ['id', 'compte_reference_username', 'montant', 'description', 
                 'date_prelevement', 'echeance', 'status']
    
    def get_status(self, obj):
        """Obtenir le statut du prélèvement"""
        if obj.echeance and obj.echeance < date.today():
            return "expiré"
        elif obj.date_prelevement <= date.today():
            return "actif"
        else:
            return "programmé" 