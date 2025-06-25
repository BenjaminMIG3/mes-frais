import jwt
import datetime
import logging
from django.conf import settings
from django.contrib.auth.models import User
from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.authentication import BaseAuthentication

# Configuration du logger
logger = logging.getLogger(__name__)

class JWTAuthentication(BaseAuthentication):
    """
    Authentification personnalisée utilisant PyJWT
    """
    
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            logger.debug("En-tête Authorization manquant")
            return None
            
        try:
            # Vérifier le format "Bearer <token>"
            parts = auth_header.split()
            if len(parts) != 2 or parts[0].lower() != 'bearer':
                logger.warning(f"Format d'en-tête Authorization invalide: {auth_header[:20]}...")
                print(f"⚠️ ERREUR AUTH - Format Authorization invalide: {auth_header[:20]}...")
                return None
                
            token = parts[1]
            logger.debug(f"Tentative de décodage du token: {token[:20]}...")
            
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=['HS256']
            )
            
            # Vérifier l'expiration
            exp = payload.get('exp')
            if exp and datetime.datetime.utcnow().timestamp() > exp:
                logger.warning(f"Token expiré pour l'utilisateur ID: {payload.get('user_id', 'N/A')}")
                print(f"⚠️ ERREUR AUTH - Token expiré pour l'utilisateur ID: {payload.get('user_id', 'N/A')}")
                raise AuthenticationFailed('Token expiré')
                
            # Récupérer l'utilisateur
            user_id = payload.get('user_id')
            if not user_id:
                logger.error("Token sans user_id")
                print(f"❌ ERREUR AUTH - Token sans user_id")
                raise AuthenticationFailed('Token invalide')
                
            user = User.objects.get(id=user_id)
            logger.info(f"Authentification réussie pour l'utilisateur: {user.username} (ID: {user.id})")
            print(f"✅ SUCCÈS AUTH - Utilisateur authentifié: {user.username} (ID: {user.id})")
            return (user, token)
            
        except jwt.InvalidTokenError as e:
            logger.warning(f"Token JWT invalide: {str(e)}")
            print(f"⚠️ ERREUR AUTH - Token JWT invalide: {str(e)}")
            raise AuthenticationFailed('Token invalide')
        except User.DoesNotExist:
            logger.error(f"Utilisateur non trouvé pour l'ID: {payload.get('user_id', 'N/A')}")
            print(f"❌ ERREUR AUTH - Utilisateur non trouvé pour l'ID: {payload.get('user_id', 'N/A')}")
            raise AuthenticationFailed('Utilisateur non trouvé')
        except Exception as e:
            logger.error(f"Erreur d'authentification inattendue: {str(e)}")
            print(f"❌ ERREUR AUTH - Exception: {str(e)}")
            raise AuthenticationFailed(f'Erreur d\'authentification: {str(e)}')


def generate_tokens(user):
    """
    Génère les tokens d'accès et de rafraîchissement
    """
    try:
        import time
        current_time = datetime.datetime.utcnow()
        
        logger.info(f"Génération de tokens pour l'utilisateur: {user.username} (ID: {user.id})")
        
        # Token d'accès (1 heure)
        access_payload = {
            'user_id': user.id,
            'username': user.username,
            'exp': current_time + datetime.timedelta(hours=1),
            'iat': current_time,
            'type': 'access',
            'jti': str(int(time.time() * 1000000))  # Identifiant unique basé sur le timestamp en microsecondes
        }
        
        # Token de rafraîchissement (7 jours)
        refresh_payload = {
            'user_id': user.id,
            'exp': current_time + datetime.timedelta(days=7),
            'iat': current_time,
            'type': 'refresh',
            'jti': str(int(time.time() * 1000000) + 1)  # Identifiant unique différent
        }
        
        access_token = jwt.encode(access_payload, settings.SECRET_KEY, algorithm='HS256')
        refresh_token = jwt.encode(refresh_payload, settings.SECRET_KEY, algorithm='HS256')
        
        logger.info(f"Tokens générés avec succès pour l'utilisateur: {user.username} (ID: {user.id})")
        print(f"✅ SUCCÈS TOKENS - Tokens générés pour: {user.username} (ID: {user.id})")
        
        return access_token, refresh_token
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens pour l'utilisateur {user.username}: {str(e)}")
        print(f"❌ ERREUR TOKENS - Génération échouée pour {user.username}: {str(e)}")
        raise


def refresh_access_token(refresh_token):
    """
    Rafraîchit le token d'accès à partir du token de rafraîchissement
    """
    try:
        logger.info("Tentative de rafraîchissement du token d'accès")
        
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=['HS256'])
        
        if payload.get('type') != 'refresh':
            logger.warning("Token de rafraîchissement avec type invalide")
            print(f"⚠️ ERREUR REFRESH - Type de token invalide: {payload.get('type')}")
            raise jwt.InvalidTokenError('Token de rafraîchissement invalide')
            
        user_id = payload.get('user_id')
        user = User.objects.get(id=user_id)
        
        logger.info(f"Rafraîchissement du token pour l'utilisateur: {user.username} (ID: {user.id})")
        
        # Générer un nouveau token d'accès avec un timestamp unique
        import time
        access_payload = {
            'user_id': user.id,
            'username': user.username,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1),
            'iat': datetime.datetime.utcnow(),
            'type': 'access',
            'jti': str(int(time.time() * 1000))  # Identifiant unique basé sur le timestamp
        }
        
        access_token = jwt.encode(access_payload, settings.SECRET_KEY, algorithm='HS256')
        
        logger.info(f"Token d'accès rafraîchi avec succès pour l'utilisateur: {user.username} (ID: {user.id})")
        print(f"✅ SUCCÈS REFRESH - Token rafraîchi pour: {user.username} (ID: {user.id})")
        
        return access_token
        
    except jwt.InvalidTokenError as e:
        logger.warning(f"Token de rafraîchissement invalide: {str(e)}")
        print(f"⚠️ ERREUR REFRESH - Token invalide: {str(e)}")
        raise AuthenticationFailed('Token de rafraîchissement invalide')
    except User.DoesNotExist:
        logger.error(f"Utilisateur non trouvé lors du rafraîchissement: {payload.get('user_id', 'N/A')}")
        print(f"❌ ERREUR REFRESH - Utilisateur non trouvé: {payload.get('user_id', 'N/A')}")
        raise AuthenticationFailed('Utilisateur non trouvé')
    except Exception as e:
        logger.error(f"Erreur inattendue lors du rafraîchissement: {str(e)}")
        print(f"❌ ERREUR REFRESH - Exception: {str(e)}")
        raise AuthenticationFailed(f'Erreur de rafraîchissement: {str(e)}') 