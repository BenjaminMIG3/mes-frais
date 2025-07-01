"""
Service pour la gestion de MongoDB
"""
from pymongo import MongoClient
from django.conf import settings
import logging
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class MongoDBService:
    """Service pour interagir avec MongoDB"""
    
    def __init__(self):
        self.client = None
        self.db = None
        self._connect()
    
    def _connect(self):
        """Établit la connexion avec MongoDB"""
        try:
            config = settings.MONGODB_CONFIG
            
            # Construction de l'URI de connexion
            if config.get('username') and config.get('password'):
                uri = f"mongodb://{config['username']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}?authSource={config['auth_source']}"
            else:
                uri = f"mongodb://{config['host']}:{config['port']}/{config['database']}"
            
            self.client = MongoClient(uri)
            self.db = self.client[config['database']]
            
            # Test de connexion
            self.client.admin.command('ping')
            logger.info("Connexion MongoDB établie avec succès")
            
        except Exception as e:
            logger.error(f"Erreur de connexion MongoDB: {e}")
            self.client = None
            self.db = None
    
    def insert_log(self, collection: str, data: Dict[str, Any]) -> Optional[str]:
        """Insère un log dans la collection spécifiée"""
        if self.db is None:
            logger.error("Connexion MongoDB non disponible")
            return None
        
        try:
            # Ajout automatique du timestamp
            data['timestamp'] = datetime.utcnow()
            data['created_at'] = datetime.utcnow()
            
            result = self.db[collection].insert_one(data)
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'insertion du log: {e}")
            return None
    
    def find_logs(self, collection: str, filter_dict: Dict[str, Any] = None, limit: int = 100) -> list:
        """Récupère les logs selon les critères"""
        if self.db is None:
            logger.error("Connexion MongoDB non disponible")
            return []
        
        try:
            filter_dict = filter_dict or {}
            cursor = self.db[collection].find(filter_dict).sort('timestamp', -1).limit(limit)
            return list(cursor)
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des logs: {e}")
            return []
    
    def delete_old_logs(self, collection: str, days_old: int = 30) -> int:
        """Supprime les logs plus anciens que X jours"""
        if self.db is None:
            logger.error("Connexion MongoDB non disponible")
            return 0
        
        try:
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            result = self.db[collection].delete_many({
                'timestamp': {'$lt': cutoff_date}
            })
            
            logger.info(f"Suppression de {result.deleted_count} logs anciens")
            return result.deleted_count
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression des logs: {e}")
            return 0
    
    def close(self):
        """Ferme la connexion MongoDB"""
        if self.client is not None:
            self.client.close()
            logger.info("Connexion MongoDB fermée")


# Instance globale du service
mongodb_service = MongoDBService() 