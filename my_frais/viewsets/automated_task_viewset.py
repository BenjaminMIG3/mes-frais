from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.db import models
from datetime import date, timedelta
from decimal import Decimal

from my_frais.models import AutomatedTask
from my_frais.serializers.automated_task_serializer import AutomatedTaskSerializer


class AutomatedTaskViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet pour consulter l'historique des tâches automatiques.
    
    Permet uniquement de lire l'historique des tâches automatiques exécutées.
    Aucune action de traitement manuel n'est disponible.
    """
    queryset = AutomatedTask.objects.all()
    serializer_class = AutomatedTaskSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['task_type', 'status', 'created_by']
    search_fields = ['error_message']
    ordering_fields = ['execution_date', 'processed_count', 'execution_duration']
    ordering = ['-execution_date']
    
    def get_queryset(self):
        """Filtrer par utilisateur connecté"""
        return super().get_queryset().filter(created_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Statistiques des tâches automatiques"""
        queryset = self.get_queryset()
        
        # Statistiques par type de tâche
        task_types = {}
        for task_type, _ in AutomatedTask.TASK_TYPES:
            count = queryset.filter(task_type=task_type).count()
            success_count = queryset.filter(task_type=task_type, status='SUCCESS').count()
            error_count = queryset.filter(task_type=task_type, status='ERROR').count()
            
            task_types[task_type] = {
                'total': count,
                'success': success_count,
                'error': error_count,
                'success_rate': (success_count / count * 100) if count > 0 else 0
            }
        
        # Statistiques par statut
        status_stats = {}
        for status_code, _ in AutomatedTask.STATUS_CHOICES:
            count = queryset.filter(status=status_code).count()
            status_stats[status_code] = count
        
        # Statistiques de performance
        successful_tasks = queryset.filter(status='SUCCESS', execution_duration__isnull=False)
        avg_duration = successful_tasks.aggregate(avg_duration=models.Avg('execution_duration'))['avg_duration'] or 0
        
        # Statistiques des 7 derniers jours
        week_ago = date.today() - timedelta(days=7)
        recent_tasks = queryset.filter(execution_date__date__gte=week_ago)
        recent_count = recent_tasks.count()
        recent_processed = recent_tasks.aggregate(total=models.Sum('processed_count'))['total'] or 0
        
        return Response({
            'task_types': task_types,
            'status_stats': status_stats,
            'performance': {
                'average_duration_seconds': float(avg_duration),
                'total_tasks': queryset.count(),
                'total_processed_operations': queryset.aggregate(total=models.Sum('processed_count'))['total'] or 0
            },
            'recent_activity': {
                'last_7_days_tasks': recent_count,
                'last_7_days_processed': recent_processed
            }
        })
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Tâches récentes (dernières 24h)"""
        yesterday = date.today() - timedelta(days=1)
        recent_tasks = self.get_queryset().filter(execution_date__date__gte=yesterday)
        
        serializer = self.get_serializer(recent_tasks, many=True)
        return Response({
            'count': recent_tasks.count(),
            'tasks': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def errors(self, request):
        """Tâches en erreur"""
        error_tasks = self.get_queryset().filter(status='ERROR').order_by('-execution_date')
        
        serializer = self.get_serializer(error_tasks, many=True)
        return Response({
            'count': error_tasks.count(),
            'tasks': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Résumé des tâches automatiques"""
        queryset = self.get_queryset()
        today = date.today()
        
        # Tâches d'aujourd'hui
        today_tasks = queryset.filter(execution_date__date=today)
        today_count = today_tasks.count()
        today_processed = today_tasks.aggregate(total=models.Sum('processed_count'))['total'] or 0
        
        # Tâches de cette semaine
        week_start = today - timedelta(days=today.weekday())
        week_tasks = queryset.filter(execution_date__date__gte=week_start)
        week_count = week_tasks.count()
        week_processed = week_tasks.aggregate(total=models.Sum('processed_count'))['total'] or 0
        
        # Tâches de ce mois
        month_start = today.replace(day=1)
        month_tasks = queryset.filter(execution_date__date__gte=month_start)
        month_count = month_tasks.count()
        month_processed = month_tasks.aggregate(total=models.Sum('processed_count'))['total'] or 0
        
        return Response({
            'today': {
                'tasks_count': today_count,
                'processed_operations': today_processed
            },
            'this_week': {
                'tasks_count': week_count,
                'processed_operations': week_processed
            },
            'this_month': {
                'tasks_count': month_count,
                'processed_operations': month_processed
            },
            'total': {
                'tasks_count': queryset.count(),
                'processed_operations': queryset.aggregate(total=models.Sum('processed_count'))['total'] or 0
            }
        }) 