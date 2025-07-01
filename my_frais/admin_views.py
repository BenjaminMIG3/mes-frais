"""
Vues admin personnalisées pour afficher les logs MongoDB
"""
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib import messages
from my_frais.admin_services import MongoDBLogService
from datetime import datetime, timedelta
import json


@staff_member_required
def logs_dashboard(request):
    """Tableau de bord des logs MongoDB"""
    try:
        # Récupérer le résumé des logs
        summary = MongoDBLogService.get_logs_summary()
        
        # Récupérer les logs récents
        recent_auth = MongoDBLogService.get_recent_logs('auth_events', 10)
        recent_errors = MongoDBLogService.get_recent_logs('errors', 10)
        recent_crud = MongoDBLogService.get_recent_logs('crud_events', 10)
        
        # Formater les logs pour l'affichage
        recent_auth = [MongoDBLogService.format_log_for_display(log) for log in recent_auth]
        recent_errors = [MongoDBLogService.format_log_for_display(log) for log in recent_errors]
        recent_crud = [MongoDBLogService.format_log_for_display(log) for log in recent_crud]
        
        context = {
            'summary': summary,
            'recent_auth': recent_auth,
            'recent_errors': recent_errors,
            'recent_crud': recent_crud,
            'title': 'Tableau de bord des logs MongoDB'
        }
        
        return render(request, 'admin/mongodb_logs/dashboard.html', context)
        
    except Exception as e:
        messages.error(request, f"Erreur lors du chargement des logs: {str(e)}")
        return render(request, 'admin/mongodb_logs/error.html', {'error': str(e)})


@staff_member_required
def logs_auth_events(request):
    """Page des logs d'authentification"""
    try:
        # Paramètres de pagination
        limit = int(request.GET.get('limit', 50))
        page = int(request.GET.get('page', 1))
        
        # Récupérer les logs
        logs = MongoDBLogService.get_recent_logs('auth_events', limit * page)
        
        # Formater les logs
        formatted_logs = [MongoDBLogService.format_log_for_display(log) for log in logs]
        
        context = {
            'logs': formatted_logs,
            'collection': 'auth_events',
            'title': 'Logs d\'authentification',
            'limit': limit,
            'page': page
        }
        
        return render(request, 'admin/mongodb_logs/logs_list.html', context)
        
    except Exception as e:
        messages.error(request, f"Erreur lors du chargement des logs: {str(e)}")
        return render(request, 'admin/mongodb_logs/error.html', {'error': str(e)})


@staff_member_required
def logs_crud_events(request):
    """Page des logs CRUD"""
    try:
        limit = int(request.GET.get('limit', 50))
        page = int(request.GET.get('page', 1))
        
        logs = MongoDBLogService.get_recent_logs('crud_events', limit * page)
        formatted_logs = [MongoDBLogService.format_log_for_display(log) for log in logs]
        
        context = {
            'logs': formatted_logs,
            'collection': 'crud_events',
            'title': 'Logs CRUD',
            'limit': limit,
            'page': page
        }
        
        return render(request, 'admin/mongodb_logs/logs_list.html', context)
        
    except Exception as e:
        messages.error(request, f"Erreur lors du chargement des logs: {str(e)}")
        return render(request, 'admin/mongodb_logs/error.html', {'error': str(e)})


@staff_member_required
def logs_errors(request):
    """Page des logs d'erreurs"""
    try:
        limit = int(request.GET.get('limit', 50))
        page = int(request.GET.get('page', 1))
        
        logs = MongoDBLogService.get_recent_logs('errors', limit * page)
        formatted_logs = [MongoDBLogService.format_log_for_display(log) for log in logs]
        
        context = {
            'logs': formatted_logs,
            'collection': 'errors',
            'title': 'Logs d\'erreurs',
            'limit': limit,
            'page': page
        }
        
        return render(request, 'admin/mongodb_logs/logs_list.html', context)
        
    except Exception as e:
        messages.error(request, f"Erreur lors du chargement des logs: {str(e)}")
        return render(request, 'admin/mongodb_logs/error.html', {'error': str(e)})


@staff_member_required
def logs_business_events(request):
    """Page des logs d'événements métier"""
    try:
        limit = int(request.GET.get('limit', 50))
        page = int(request.GET.get('page', 1))
        
        logs = MongoDBLogService.get_recent_logs('business_events', limit * page)
        formatted_logs = [MongoDBLogService.format_log_for_display(log) for log in logs]
        
        context = {
            'logs': formatted_logs,
            'collection': 'business_events',
            'title': 'Logs d\'événements métier',
            'limit': limit,
            'page': page
        }
        
        return render(request, 'admin/mongodb_logs/logs_list.html', context)
        
    except Exception as e:
        messages.error(request, f"Erreur lors du chargement des logs: {str(e)}")
        return render(request, 'admin/mongodb_logs/error.html', {'error': str(e)})


@method_decorator(staff_member_required, name='dispatch')
class LogsAPIView(View):
    """Vue API pour les logs (AJAX)"""
    
    def get(self, request, collection):
        """Récupérer des logs via AJAX"""
        try:
            limit = int(request.GET.get('limit', 50))
            logs = MongoDBLogService.get_recent_logs(collection, limit)
            formatted_logs = [MongoDBLogService.format_log_for_display(log) for log in logs]
            
            return JsonResponse({
                'success': True,
                'logs': formatted_logs
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    def delete(self, request, collection):
        """Supprimer les anciens logs"""
        try:
            days_old = int(request.POST.get('days_old', 30))
            deleted_counts = MongoDBLogService.delete_old_logs(days_old)
            
            messages.success(request, f"Logs supprimés: {deleted_counts}")
            
            return JsonResponse({
                'success': True,
                'deleted_counts': deleted_counts
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500) 