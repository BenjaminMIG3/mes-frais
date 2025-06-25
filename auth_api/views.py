from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from auth_api.auth_serializer import AuthSerializer
from auth_api.jwt_auth import generate_tokens, refresh_access_token


class AuthViewSet(viewsets.ViewSet):
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        """Connexion avec génération de tokens JWT"""
        serializer = AuthSerializer(data=request.data)
        if serializer.is_valid():
            validated = serializer.validated_data
            user = validated.get('user')
            if user is not None:
                # Génération des tokens JWT avec notre implémentation
                access_token, refresh_token = generate_tokens(user)
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
                return Response({'message': 'Identifiants invalides.'}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        """Inscription avec génération automatique de tokens JWT"""
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email')
        
        if not username or not password or not email:
            return Response({'message': 'Champs manquants.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(username=username).exists():
            return Response({'message': 'Nom d\'utilisateur déjà utilisé.'}, status=status.HTTP_409_CONFLICT)
        
        if User.objects.filter(email=email).exists():
            return Response({'message': 'Email déjà utilisé.'}, status=status.HTTP_409_CONFLICT)
        
        user = User.objects.create_user(username=username, email=email, password=password)
        
        # Génération des tokens JWT pour l'utilisateur nouvellement créé
        access_token, refresh_token = generate_tokens(user)
        
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

    @action(detail=False, methods=['post'])
    def refresh_token(self, request):
        """Rafraîchissement du token d'accès"""
        refresh_token = request.data.get('refresh_token')
        
        if not refresh_token:
            return Response({'message': 'Token de rafraîchissement requis.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            access_token = refresh_access_token(refresh_token)
            return Response({
                'access_token': access_token,
                'message': 'Token rafraîchi avec succès'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'message': 'Token de rafraîchissement invalide.'}, status=status.HTTP_401_UNAUTHORIZED)

    @action(detail=False, methods=['post'])
    def logout(self, request):
        """Déconnexion (sans blacklist pour simplifier)"""
        # Note: Pour une implémentation complète, vous pourriez ajouter
        # une table de blacklist pour les tokens révoqués
        return Response({'message': 'Déconnexion réussie'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def profile(self, request):
        """Récupération du profil utilisateur (endpoint protégé)"""
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