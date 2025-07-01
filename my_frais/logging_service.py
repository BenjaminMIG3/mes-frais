"""
Service de logging centralisé pour l'application
"""
from my_frais.mongodb_service import mongodb_service
from django.contrib.auth.models import User
from django.http import HttpRequest
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import traceback
import json

logger = logging.getLogger(__name__)


class ApplicationLogger:
    """Service de logging centralisé pour tous les événements de l'application"""
    
    @staticmethod
    def _get_user_info(user) -> Dict[str, Any]:
        """Extrait les informations de l'utilisateur"""
        if user and user.is_authenticated:
            return {
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser
            }
        return {'user_id': None, 'username': 'anonymous'}
    
    @staticmethod
    def _get_request_info(request: HttpRequest) -> Dict[str, Any]:
        """Extrait les informations de la requête"""
        return {
            'ip_address': request.META.get('REMOTE_ADDR'),
            'user_agent': request.META.get('HTTP_USER_AGENT'),
            'method': request.method,
            'path': request.path,
            'query_params': dict(request.GET.items()),
            'content_type': request.content_type
        }
    
    @staticmethod
    def log_auth_event(event_type: str, user: User = None, request: HttpRequest = None, 
                      success: bool = True, details: Dict[str, Any] = None):
        """Log les événements d'authentification"""
        log_data = {
            'event_type': event_type,
            'category': 'authentication',
            'success': success,
            'timestamp': datetime.utcnow(),
            'details': details or {}
        }
        
        if user:
            log_data['user_info'] = ApplicationLogger._get_user_info(user)
        
        if request:
            log_data['request_info'] = ApplicationLogger._get_request_info(request)
        
        mongodb_service.insert_log('auth_events', log_data)
    
    @staticmethod
    def log_crud_event(event_type: str, model_name: str, object_id: int = None, 
                      user: User = None, request: HttpRequest = None, 
                      old_data: Dict[str, Any] = None, new_data: Dict[str, Any] = None):
        """Log les événements CRUD (Create, Read, Update, Delete)"""
        log_data = {
            'event_type': event_type,  # 'create', 'update', 'delete', 'read'
            'category': 'crud',
            'model_name': model_name,
            'object_id': object_id,
            'timestamp': datetime.utcnow(),
            'old_data': old_data,
            'new_data': new_data
        }
        
        if user:
            log_data['user_info'] = ApplicationLogger._get_user_info(user)
        
        if request:
            log_data['request_info'] = ApplicationLogger._get_request_info(request)
        
        mongodb_service.insert_log('crud_events', log_data)
    
    @staticmethod
    def log_error(error: Exception, user: User = None, request: HttpRequest = None, 
                 context: Dict[str, Any] = None):
        """Log les erreurs de l'application"""
        log_data = {
            'event_type': 'error',
            'category': 'error',
            'error_type': type(error).__name__,
            'error_message': str(error),
            'error_traceback': traceback.format_exc(),
            'timestamp': datetime.utcnow(),
            'context': context or {}
        }
        
        if user:
            log_data['user_info'] = ApplicationLogger._get_user_info(user)
        
        if request:
            log_data['request_info'] = ApplicationLogger._get_request_info(request)
        
        mongodb_service.insert_log('errors', log_data)
    
    @staticmethod
    def log_business_event(event_type: str, category: str, user: User = None, 
                          request: HttpRequest = None, details: Dict[str, Any] = None):
        """Log les événements métier spécifiques"""
        log_data = {
            'event_type': event_type,
            'category': category,
            'timestamp': datetime.utcnow(),
            'details': details or {}
        }
        
        if user:
            log_data['user_info'] = ApplicationLogger._get_user_info(user)
        
        if request:
            log_data['request_info'] = ApplicationLogger._get_request_info(request)
        
        mongodb_service.insert_log('business_events', log_data)


# Instance globale du logger
app_logger = ApplicationLogger() 