from rest_framework import serializers
from my_frais.models import AutomatedTask


class AutomatedTaskSerializer(serializers.ModelSerializer):
    """Serializer pour les tâches automatiques"""
    
    task_type_display = serializers.CharField(source='get_task_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    execution_date_formatted = serializers.SerializerMethodField()
    execution_duration_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = AutomatedTask
        fields = [
            'id', 'task_type', 'task_type_display', 'status', 'status_display',
            'processed_count', 'error_message', 'execution_date', 'execution_date_formatted',
            'execution_duration', 'execution_duration_formatted', 'details',
            'created_by', 'created_by_username', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'task_type', 'status', 'processed_count', 'error_message',
            'execution_date', 'execution_duration', 'details', 'created_by',
            'created_at', 'updated_at'
        ]
    
    def get_execution_date_formatted(self, obj):
        """Formatage de la date d'exécution"""
        if obj.execution_date:
            return obj.execution_date.strftime('%d/%m/%Y %H:%M:%S')
        return None
    
    def get_execution_duration_formatted(self, obj):
        """Formatage de la durée d'exécution"""
        if obj.execution_duration:
            return f"{obj.execution_duration:.3f}s"
        return "N/A"


class AutomatedTaskListSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour la liste des tâches automatiques"""
    
    task_type_display = serializers.CharField(source='get_task_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    execution_date_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = AutomatedTask
        fields = [
            'id', 'task_type', 'task_type_display', 'status', 'status_display',
            'processed_count', 'execution_date', 'execution_date_formatted',
            'execution_duration'
        ]
    
    def get_execution_date_formatted(self, obj):
        """Formatage de la date d'exécution"""
        if obj.execution_date:
            return obj.execution_date.strftime('%d/%m/%Y %H:%M:%S')
        return None 