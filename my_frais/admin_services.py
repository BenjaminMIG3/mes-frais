"""
Service pour afficher les logs MongoDB dans l'admin Django
"""
from my_frais.mongodb_service import mongodb_service
from django.utils import timezone
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json


class MongoDBLogService:
    """Service pour gérer l'affichage des logs MongoDB dans l'admin"""
    
    @staticmethod
    def get_logs_summary() -> Dict[str, int]:
        """Récupère un résumé des logs par collection"""
        collections = ['auth_events', 'crud_events', 'errors', 'business_events']
        summary = {}
        
        for collection in collections:
            try:
                count = mongodb_service.db[collection].count_documents({})
                summary[collection] = count
            except Exception:
                summary[collection] = 0
        
        return summary
    
    @staticmethod
    def get_recent_logs(collection: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Récupère les logs récents d'une collection"""
        try:
            logs = mongodb_service.find_logs(collection, limit=limit)
            return logs
        except Exception:
            return []
    
    @staticmethod
    def get_logs_by_date_range(collection: str, start_date: datetime, end_date: datetime, limit: int = 100) -> List[Dict[str, Any]]:
        """Récupère les logs dans une plage de dates"""
        try:
            filter_dict = {
                'timestamp': {
                    '$gte': start_date,
                    '$lte': end_date
                }
            }
            logs = mongodb_service.find_logs(collection, filter_dict, limit)
            return logs
        except Exception:
            return []
    
    @staticmethod
    def get_logs_by_user(user_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """Récupère les logs d'un utilisateur spécifique"""
        try:
            filter_dict = {'user_info.user_id': user_id}
            logs = mongodb_service.find_logs('auth_events', filter_dict, limit)
            logs.extend(mongodb_service.find_logs('crud_events', filter_dict, limit))
            logs.extend(mongodb_service.find_logs('business_events', filter_dict, limit))
            return sorted(logs, key=lambda x: x.get('timestamp', datetime.min), reverse=True)
        except Exception:
            return []
    
    @staticmethod
    def get_error_logs(limit: int = 100) -> List[Dict[str, Any]]:
        """Récupère les logs d'erreurs"""
        try:
            logs = mongodb_service.find_logs('errors', limit=limit)
            return logs
        except Exception:
            return []
    
    @staticmethod
    def format_log_for_display(log: Dict[str, Any]) -> Dict[str, Any]:
        """Formate un log pour l'affichage dans l'admin"""
        formatted = log.copy()
        
        # Formater le timestamp
        if 'timestamp' in formatted:
            if isinstance(formatted['timestamp'], datetime):
                formatted['timestamp_display'] = formatted['timestamp'].strftime('%d/%m/%Y %H:%M:%S')
            else:
                formatted['timestamp_display'] = str(formatted['timestamp'])
        
        # Formater les détails JSON
        if 'details' in formatted and formatted['details']:
            formatted['details_display'] = json.dumps(formatted['details'], indent=2, ensure_ascii=False)
        
        if 'old_data' in formatted and formatted['old_data']:
            formatted['old_data_display'] = json.dumps(formatted['old_data'], indent=2, ensure_ascii=False)
        
        if 'new_data' in formatted and formatted['new_data']:
            formatted['new_data_display'] = json.dumps(formatted['new_data'], indent=2, ensure_ascii=False)
        
        # Formater les informations utilisateur
        if 'user_info' in formatted:
            user_info = formatted['user_info']
            formatted['user_display'] = f"{user_info.get('username', 'N/A')} (ID: {user_info.get('user_id', 'N/A')})"
        
        # Formater les informations de requête
        if 'request_info' in formatted:
            req_info = formatted['request_info']
            formatted['request_display'] = f"{req_info.get('method', 'N/A')} {req_info.get('path', 'N/A')} - {req_info.get('ip_address', 'N/A')}"
        
        return formatted
    
    @staticmethod
    def delete_old_logs(days_old: int = 30) -> Dict[str, int]:
        """Supprime les logs anciens et retourne le nombre de logs supprimés par collection"""
        collections = ['auth_events', 'crud_events', 'errors', 'business_events']
        deleted_counts = {}
        
        for collection in collections:
            try:
                count = mongodb_service.delete_old_logs(collection, days_old)
                deleted_counts[collection] = count
            except Exception:
                deleted_counts[collection] = 0
        
        return deleted_counts 