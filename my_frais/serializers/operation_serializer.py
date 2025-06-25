from rest_framework import serializers
from my_frais.models import Operation, Account
from decimal import Decimal


class OperationSerializer(serializers.ModelSerializer):
    compte_reference_username = serializers.CharField(source='compte_reference.user.username', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Operation
        fields = [
            'id', 'compte_reference', 'compte_reference_username', 
            'montant', 'description', 'created_by', 'created_by_username',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_by_username', 'created_at', 'updated_at']
    
    def validate_montant(self, value):
        """Validation du montant - doit être différent de zéro"""
        if value == Decimal('0.00'):
            raise serializers.ValidationError("Le montant ne peut pas être zéro.")
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
    
    def create(self, validated_data):
        """Création d'une opération avec mise à jour automatique du solde"""
        validated_data['created_by'] = self.context['request'].user
        
        # Créer l'opération
        operation = super().create(validated_data)
        
        # Mettre à jour le solde du compte
        compte = operation.compte_reference
        compte.solde += operation.montant
        compte.save()
        
        return operation
    
    def update(self, instance, validated_data):
        """Mise à jour d'une opération avec ajustement du solde"""
        # Sauvegarder l'ancien montant pour ajuster le solde
        ancien_montant = instance.montant
        
        # Mettre à jour l'opération
        operation = super().update(instance, validated_data)
        
        # Ajuster le solde du compte
        compte = operation.compte_reference
        nouveau_montant = operation.montant
        difference = nouveau_montant - ancien_montant
        compte.solde += difference
        compte.save()
        
        return operation
    
    def delete(self, instance):
        """Suppression d'une opération avec ajustement du solde"""
        # Ajuster le solde du compte avant suppression
        compte = instance.compte_reference
        compte.solde -= instance.montant
        compte.save()
        
        # Supprimer l'opération
        instance.delete()


class OperationListSerializer(serializers.ModelSerializer):
    """Serializer pour la liste des opérations avec informations résumées"""
    compte_reference_username = serializers.CharField(source='compte_reference.user.username', read_only=True)
    
    class Meta:
        model = Operation
        fields = ['id', 'compte_reference_username', 'montant', 'description', 'created_at'] 