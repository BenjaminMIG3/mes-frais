import jwt
import datetime
from django.conf import settings
from django.contrib.auth.models import User
from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.authentication import BaseAuthentication


class JWTAuthentication(BaseAuthentication):
    """
    Authentification personnalisée utilisant PyJWT
    """
    
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None
            
        try:
            # Vérifier le format "Bearer <token>"
            parts = auth_header.split()
            if len(parts) != 2 or parts[0].lower() != 'bearer':
                return None
                
            token = parts[1]
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=['HS256']
            )
            
            # Vérifier l'expiration
            exp = payload.get('exp')
            if exp and datetime.datetime.utcnow().timestamp() > exp:
                raise AuthenticationFailed('Token expiré')
                
            # Récupérer l'utilisateur
            user_id = payload.get('user_id')
            if not user_id:
                raise AuthenticationFailed('Token invalide')
                
            user = User.objects.get(id=user_id)
            return (user, token)
            
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Token invalide')
        except User.DoesNotExist:
            raise AuthenticationFailed('Utilisateur non trouvé')
        except Exception as e:
            raise AuthenticationFailed(f'Erreur d\'authentification: {str(e)}')


def generate_tokens(user):
    """
    Génère les tokens d'accès et de rafraîchissement
    """
    import time
    current_time = datetime.datetime.utcnow()
    
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
    
    return access_token, refresh_token


def refresh_access_token(refresh_token):
    """
    Rafraîchit le token d'accès à partir du token de rafraîchissement
    """
    try:
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=['HS256'])
        
        if payload.get('type') != 'refresh':
            raise jwt.InvalidTokenError('Token de rafraîchissement invalide')
            
        user_id = payload.get('user_id')
        user = User.objects.get(id=user_id)
        
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
        return access_token
        
    except jwt.InvalidTokenError:
        raise AuthenticationFailed('Token de rafraîchissement invalide')
    except User.DoesNotExist:
        raise AuthenticationFailed('Utilisateur non trouvé') 