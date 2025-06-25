from rest_framework import serializers
from my_frais.models import Account
from django.contrib.auth.models import User


class AccountSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Account
        fields = [
            'id', 'user', 'user_username', 'nom', 'solde', 
            'created_by', 'created_by_username', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_by_username', 'created_at', 'updated_at']
    
    def validate_solde(self, value):
        """Validation du solde - doit être positif"""
        if value < 0:
            raise serializers.ValidationError("Le solde ne peut pas être négatif.")
        return value
    
    def validate_user(self, value):
        """Validation de l'utilisateur - doit exister"""
        if not User.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("L'utilisateur spécifié n'existe pas.")
        return value
    
    def create(self, validated_data):
        """Création d'un compte avec l'utilisateur connecté comme créateur"""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Mise à jour d'un compte"""
        # Empêcher la modification de l'utilisateur propriétaire
        if 'user' in validated_data:
            del validated_data['user']
        return super().update(instance, validated_data)


class AccountListSerializer(serializers.ModelSerializer):
    """Serializer pour la liste des comptes avec informations résumées"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    operations_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Account
        fields = ['id', 'user_username', 'nom', 'solde', 'operations_count', 'updated_at']
    
    def get_operations_count(self, obj):
        """Compter le nombre d'opérations pour ce compte"""
        return obj.operations.count()


class AccountSummarySerializer(serializers.ModelSerializer):
    """Serializer pour le résumé des comptes avec statistiques complètes"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    operations_count = serializers.SerializerMethodField()
    direct_debits_count = serializers.SerializerMethodField()
    recurring_incomes_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Account
        fields = ['id', 'user_username', 'nom', 'solde', 'operations_count', 'direct_debits_count', 'recurring_incomes_count', 'created_at', 'updated_at']
    
    def get_operations_count(self, obj):
        """Compter le nombre d'opérations pour ce compte"""
        return obj.operations.count()
    
    def get_direct_debits_count(self, obj):
        """Compter le nombre de prélèvements automatiques pour ce compte"""
        return obj.operations.filter(directdebit__actif=True).count()
    
    def get_recurring_incomes_count(self, obj):
        """Compter le nombre de revenus récurrents pour ce compte"""
        return obj.recurring_incomes.filter(actif=True).count() 