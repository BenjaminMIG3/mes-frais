"""
Middleware pour le logging automatique des requêtes et erreurs
"""
from my_frais.logging_service import app_logger
from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin
import time
import logging

logger = logging.getLogger(__name__)


class LoggingMiddleware(MiddlewareMixin):
    """Middleware pour logger automatiquement les requêtes et erreurs"""
    
    def process_request(self, request: HttpRequest):
        """Log le début de la requête"""
        request.start_time = time.time()
        
        # Log des tentatives d'accès aux endpoints sensibles
        if request.path.startswith('/admin/'):
            app_logger.log_business_event(
                event_type='admin_access_attempt',
                category='security',
                request=request,
                details={'path': request.path}
            )
    
    def process_response(self, request: HttpRequest, response: HttpResponse):
        """Log la fin de la requête"""
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            
            # Log des requêtes lentes (> 2 secondes)
            if duration > 2.0:
                app_logger.log_business_event(
                    event_type='slow_request',
                    category='performance',
                    request=request,
                    details={
                        'duration': duration,
                        'status_code': response.status_code
                    }
                )
            
            # Log des erreurs 4xx et 5xx
            if response.status_code >= 400:
                app_logger.log_business_event(
                    event_type='http_error',
                    category='error',
                    request=request,
                    details={
                        'status_code': response.status_code,
                        'duration': duration
                    }
                )
        
        return response
    
    def process_exception(self, request: HttpRequest, exception):
        """Log les exceptions non gérées"""
        app_logger.log_error(
            error=exception,
            request=request,
            context={'path': request.path, 'method': request.method}
        )
        return None 