import logging
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from auth_api.auth_serializer import AuthSerializer
from auth_api.jwt_auth import generate_tokens, refresh_access_token

# Configuration du logger
logger = logging.getLogger(__name__)

class AuthViewSet(viewsets.ViewSet):
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        """Connexion avec génération de tokens JWT"""
        try:
            logger.info(f"Tentative de connexion pour l'utilisateur: {request.data.get('username', 'N/A')}")

            print(f"Données reçues: {request.data}")
            
            serializer = AuthSerializer(data=request.data)
            if serializer.is_valid():
                validated = serializer.validated_data
                user = validated.get('user')
                if user is not None:
                    # Génération des tokens JWT avec notre implémentation
                    access_token, refresh_token = generate_tokens(user)
                    logger.info(f"Connexion réussie pour l'utilisateur: {user.username} (ID: {user.id})")
                    return Response({
                        'message': 'Connexion réussie',
                        'access_token': access_token,
                        'refresh_token': refresh_token,
                        'user': {
                            'id': user.id,
                            'username': user.username,
                            'email': user.email
                        }
                    }, status=status.HTTP_200_OK)
                else:
                    logger.warning(f"Identifiants invalides pour l'utilisateur: {request.data.get('username', 'N/A')}")
                    return Response({'message': 'Identifiants invalides.'}, status=status.HTTP_401_UNAUTHORIZED)
            else:
                # Peut tu ajouter la forme attendue pour le login ?
                print(f"❌ ERREUR LOGIN - Validation échouée: {serializer.errors}")
                print(f"📋 FORME ATTENDUE LOGIN: {{'username': 'email@example.com', 'password': 'motdepasse123'}}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"❌ ERREUR LOGIN - Exception: {str(e)}")
            return Response({'message': 'Erreur interne du serveur.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        """Inscription avec génération automatique de tokens JWT"""
        try:
            username = request.data.get('username')
            password = request.data.get('password')
            email = request.data.get('email')
            
            logger.info(f"Tentative d'inscription pour l'utilisateur: {username}")
            
            if not username or not password or not email:
                print(f"⚠️ ERREUR REGISTER - Champs manquants: username={bool(username)}, password={bool(password)}, email={bool(email)}")
                print(f"📋 FORME ATTENDUE REGISTER: {{'username': 'email@example.com', 'password': 'motdepasse123', 'email': 'email@example.com'}}")
                return Response({'message': 'Champs manquants.'}, status=status.HTTP_400_BAD_REQUEST)
            
            if User.objects.filter(username=username).exists():
                print(f"⚠️ ERREUR REGISTER - Username déjà utilisé: {username}")
                return Response({'message': 'Nom d\'utilisateur déjà utilisé.'}, status=status.HTTP_409_CONFLICT)
            
            if User.objects.filter(email=email).exists():
                print(f"⚠️ ERREUR REGISTER - Email déjà utilisé: {email}")
                return Response({'message': 'Email déjà utilisé.'}, status=status.HTTP_409_CONFLICT)
            
            user = User.objects.create_user(username=username, email=email, password=password)
            
            # Génération des tokens JWT pour l'utilisateur nouvellement créé
            access_token, refresh_token = generate_tokens(user)
            
            print(f"✅ SUCCÈS REGISTER - Nouvel utilisateur créé: {username} (ID: {user.id})")
            
            return Response({
                'message': 'Inscription réussie',
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            print(f"❌ ERREUR REGISTER - Exception: {str(e)}")
            return Response({'message': 'Erreur interne du serveur.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def refresh_token(self, request):
        """Rafraîchissement du token d'accès"""
        try:
            refresh_token = request.data.get('refresh_token')
            
            logger.info(f"Tentative de rafraîchissement de token")
            
            if not refresh_token:
                print(f"⚠️ ERREUR REFRESH - Token de rafraîchissement manquant")
                print(f"📋 FORME ATTENDUE REFRESH: {{'refresh_token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'}}")
                return Response({'message': 'Token de rafraîchissement requis.'}, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                access_token = refresh_access_token(refresh_token)
                print(f"✅ SUCCÈS REFRESH - Token rafraîchi")
                return Response({
                    'access_token': access_token,
                    'message': 'Token rafraîchi avec succès'
                }, status=status.HTTP_200_OK)
            except Exception as e:
                print(f"⚠️ ERREUR REFRESH - Token invalide: {str(e)}")
                return Response({'message': 'Token de rafraîchissement invalide.'}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            print(f"❌ ERREUR REFRESH - Exception: {str(e)}")
            return Response({'message': 'Erreur interne du serveur.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def logout(self, request):
        """Déconnexion (sans blacklist pour simplifier)"""
        try:
            print(f"✅ SUCCÈS LOGOUT - Utilisateur déconnecté: {request.user.username} (ID: {request.user.id})")
            # Note: Pour une implémentation complète, vous pourriez ajouter
            # une table de blacklist pour les tokens révoqués
            return Response({'message': 'Déconnexion réussie'}, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"❌ ERREUR LOGOUT - Exception: {str(e)}")
            print(f"📋 EN-TÊTE ATTENDU: Authorization: Bearer <access_token>")
            return Response({'message': 'Erreur interne du serveur.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def profile(self, request):
        """Récupération du profil utilisateur (endpoint protégé)"""
        try:
            print(f"✅ SUCCÈS PROFILE - Profil récupéré: {request.user.username} (ID: {request.user.id})")
            return Response({
                'user': {
                    'id': request.user.id,
                    'username': request.user.username,
                    'email': request.user.email,
                    'first_name': request.user.first_name,
                    'last_name': request.user.last_name,
                    'date_joined': request.user.date_joined
                }
            }, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"❌ ERREUR PROFILE - Exception: {str(e)}")
            print(f"📋 EN-TÊTE ATTENDU: Authorization: Bearer <access_token>")
            return Response({'message': 'Erreur interne du serveur.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 