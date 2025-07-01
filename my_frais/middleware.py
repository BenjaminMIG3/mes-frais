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
    
    def _should_log_request(self, request: HttpRequest) -> bool:
        """Détermine si une requête doit être loggée"""
        # Exclure les requêtes de l'interface admin
        if request.path.startswith('/admin/'):
            return False
        
        # Exclure les requêtes pour les fichiers statiques
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            return False
        
        # Exclure les requêtes de santé/health check
        if request.path in ['/health/', '/ping/', '/status/']:
            return False
        
        # Exclure les requêtes OPTIONS (CORS preflight)
        if request.method == 'OPTIONS':
            return False
        
        # Exclure les requêtes de robots/crawlers
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        bot_indicators = ['bot', 'crawler', 'spider', 'scraper']
        if any(indicator in user_agent for indicator in bot_indicators):
            return False
        
        return True
    
    def process_request(self, request: HttpRequest):
        """Log le début de la requête"""
        request.start_time = time.time()
        
        # Log des tentatives d'accès aux endpoints sensibles (sauf admin)
        if request.path.startswith('/api/') and 'admin' in request.path:
            if self._should_log_request(request):
                app_logger.log_business_event(
                    event_type='admin_api_access_attempt',
                    category='security',
                    request=request,
                    details={'path': request.path}
                )
    
    def process_response(self, request: HttpRequest, response: HttpResponse):
        """Log la fin de la requête"""
        if not self._should_log_request(request):
            return response
            
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            
            # Log des requêtes lentes (> 2 secondes) - seulement pour les API
            if duration > 2.0 and request.path.startswith('/api/'):
                app_logger.log_business_event(
                    event_type='slow_request',
                    category='performance',
                    request=request,
                    details={
                        'duration': duration,
                        'status_code': response.status_code,
                        'path': request.path
                    }
                )
            
            # Log des erreurs 4xx et 5xx - seulement pour les API et pages importantes
            if response.status_code >= 400 and (
                request.path.startswith('/api/') or 
                request.path in ['/', '/login/', '/register/']
            ):
                app_logger.log_business_event(
                    event_type='http_error',
                    category='error',
                    request=request,
                    details={
                        'status_code': response.status_code,
                        'duration': duration,
                        'path': request.path
                    }
                )
        
        return response
    
    def process_exception(self, request: HttpRequest, exception):
        """Log les exceptions non gérées"""
        if self._should_log_request(request):
            app_logger.log_error(
                error=exception,
                request=request,
                context={'path': request.path, 'method': request.method}
            )
        return None 