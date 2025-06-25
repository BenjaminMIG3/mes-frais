import json
import jwt
from datetime import datetime, timedelta
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.conf import settings
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock

from auth_api.auth_serializer import AuthSerializer
from auth_api.jwt_auth import JWTAuthentication, generate_tokens, refresh_access_token
from auth_api.views import AuthViewSet


class AuthSerializerTestCase(TestCase):
    """Tests pour le serializer d'authentification"""
    
    def setUp(self):
        """Configuration initiale pour chaque test"""
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpassword123'
        )
    
    def test_serializer_valid_data(self):
        """Test avec des données valides"""
        data = {
            'username': 'testuser@example.com',
            'password': 'testpassword123'
        }
        serializer = AuthSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['user'], self.user)
    
    def test_serializer_invalid_email_format(self):
        """Test avec un format d'email invalide"""
        data = {
            'username': 'invalid-email',
            'password': 'testpassword123'
        }
        serializer = AuthSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('Adresse mail invalide', str(serializer.errors))
    
    def test_serializer_missing_username(self):
        """Test avec nom d'utilisateur manquant"""
        data = {
            'password': 'testpassword123'
        }
        serializer = AuthSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('username', serializer.errors)
    
    def test_serializer_missing_password(self):
        """Test avec mot de passe manquant"""
        data = {
            'username': 'testuser@example.com'
        }
        serializer = AuthSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)
    
    def test_serializer_invalid_credentials(self):
        """Test avec des identifiants incorrects"""
        data = {
            'username': 'testuser@example.com',
            'password': 'wrongpassword'
        }
        serializer = AuthSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('Identifiants invalides', str(serializer.errors))


class JWTAuthenticationTestCase(TestCase):
    """Tests pour l'authentification JWT"""
    
    def setUp(self):
        """Configuration initiale pour chaque test"""
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpassword123'
        )
        self.authentication = JWTAuthentication()
    
    def test_generate_tokens(self):
        """Test de génération des tokens"""
        access_token, refresh_token = generate_tokens(self.user)
        
        # Vérifier que les tokens sont des strings non vides
        self.assertIsInstance(access_token, str)
        self.assertIsInstance(refresh_token, str)
        self.assertTrue(len(access_token) > 0)
        self.assertTrue(len(refresh_token) > 0)
        
        # Décoder et vérifier le contenu des tokens
        access_payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=['HS256'])
        refresh_payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=['HS256'])
        
        self.assertEqual(access_payload['user_id'], self.user.id)
        self.assertEqual(access_payload['username'], self.user.username)
        self.assertEqual(access_payload['type'], 'access')
        
        self.assertEqual(refresh_payload['user_id'], self.user.id)
        self.assertEqual(refresh_payload['type'], 'refresh')
    
    def test_valid_token_authentication(self):
        """Test d'authentification avec un token valide"""
        access_token, _ = generate_tokens(self.user)
        
        # Créer une requête mock avec l'en-tête Authorization
        request = MagicMock()
        request.headers = {'Authorization': f'Bearer {access_token}'}
        
        result = self.authentication.authenticate(request)
        
        self.assertIsNotNone(result)
        user, token = result
        self.assertEqual(user.id, self.user.id)
        self.assertEqual(token, access_token)
    
    def test_missing_authorization_header(self):
        """Test sans en-tête Authorization"""
        request = MagicMock()
        request.headers = {}
        
        result = self.authentication.authenticate(request)
        self.assertIsNone(result)
    
    def test_invalid_authorization_format(self):
        """Test avec un format d'en-tête Authorization invalide"""
        request = MagicMock()
        request.headers = {'Authorization': 'InvalidFormat token'}
        
        result = self.authentication.authenticate(request)
        self.assertIsNone(result)
    
    def test_expired_token(self):
        """Test avec un token expiré"""
        # Créer un token expiré
        expired_payload = {
            'user_id': self.user.id,
            'username': self.user.username,
            'exp': datetime.utcnow() - timedelta(hours=1),  # Expiré
            'iat': datetime.utcnow() - timedelta(hours=2),
            'type': 'access'
        }
        expired_token = jwt.encode(expired_payload, settings.SECRET_KEY, algorithm='HS256')
        
        request = MagicMock()
        request.headers = {'Authorization': f'Bearer {expired_token}'}
        
        with self.assertRaises(Exception):
            self.authentication.authenticate(request)
    
    def test_refresh_access_token(self):
        """Test de rafraîchissement du token d'accès"""
        _, refresh_token = generate_tokens(self.user)
        
        new_access_token = refresh_access_token(refresh_token)
        
        self.assertIsInstance(new_access_token, str)
        self.assertTrue(len(new_access_token) > 0)
        
        # Vérifier le contenu du nouveau token
        payload = jwt.decode(new_access_token, settings.SECRET_KEY, algorithms=['HS256'])
        self.assertEqual(payload['user_id'], self.user.id)
        self.assertEqual(payload['type'], 'access')
    
    def test_refresh_with_invalid_token(self):
        """Test de rafraîchissement avec un token invalide"""
        invalid_token = 'invalid.token.here'
        
        with self.assertRaises(Exception):
            refresh_access_token(invalid_token)


class AuthViewSetTestCase(APITestCase):
    """Tests pour les vues d'authentification"""
    
    def setUp(self):
        """Configuration initiale pour chaque test"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpassword123',
            first_name='John',
            last_name='Doe'
        )
        
        # URLs des endpoints
        self.login_url = '/api/v1/auth/login/'
        self.register_url = '/api/v1/auth/register/'
        self.refresh_url = '/api/v1/auth/refresh_token/'
        self.logout_url = '/api/v1/auth/logout/'
        self.profile_url = '/api/v1/auth/profile/'
    
    def test_login_success(self):
        """Test de connexion réussie"""
        data = {
            'username': 'testuser@example.com',
            'password': 'testpassword123'
        }
        response = self.client.post(self.login_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.data)
        self.assertIn('refresh_token', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['username'], self.user.username)
        self.assertEqual(response.data['message'], 'Connexion réussie')
    
    def test_login_invalid_credentials(self):
        """Test de connexion avec des identifiants invalides"""
        data = {
            'username': 'testuser@example.com',
            'password': 'wrongpassword'
        }
        response = self.client.post(self.login_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_login_missing_fields(self):
        """Test de connexion avec des champs manquants"""
        data = {
            'username': 'testuser@example.com'
            # Mot de passe manquant
        }
        response = self.client.post(self.login_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_register_success(self):
        """Test d'inscription réussie"""
        data = {
            'username': 'newuser@example.com',
            'email': 'newuser@example.com',
            'password': 'newpassword123'
        }
        response = self.client.post(self.register_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access_token', response.data)
        self.assertIn('refresh_token', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['message'], 'Inscription réussie')
        
        # Vérifier que l'utilisateur a été créé
        new_user = User.objects.get(username='newuser@example.com')
        self.assertEqual(new_user.email, 'newuser@example.com')
    
    def test_register_duplicate_username(self):
        """Test d'inscription avec un nom d'utilisateur existant"""
        data = {
            'username': 'testuser@example.com',  # Déjà existant
            'email': 'different@example.com',
            'password': 'newpassword123'
        }
        response = self.client.post(self.register_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn('déjà utilisé', response.data['message'])
    
    def test_register_duplicate_email(self):
        """Test d'inscription avec un email existant"""
        data = {
            'username': 'newuser@example.com',
            'email': 'testuser@example.com',  # Déjà existant
            'password': 'newpassword123'
        }
        response = self.client.post(self.register_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn('déjà utilisé', response.data['message'])
    
    def test_register_missing_fields(self):
        """Test d'inscription avec des champs manquants"""
        data = {
            'username': 'newuser@example.com'
            # Email et mot de passe manquants
        }
        response = self.client.post(self.register_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('manquants', response.data['message'])
    
    def test_refresh_token_success(self):
        """Test de rafraîchissement de token réussi"""
        access_token, refresh_token = generate_tokens(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        data = {
            'refresh_token': refresh_token
        }
        response = self.client.post(self.refresh_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.data)
        self.assertEqual(response.data['message'], 'Token rafraîchi avec succès')
    
    def test_refresh_token_missing(self):
        """Test de rafraîchissement sans token"""
        access_token, _ = generate_tokens(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        data = {}
        response = self.client.post(self.refresh_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('requis', response.data['message'])
    
    def test_refresh_token_invalid(self):
        """Test de rafraîchissement avec token invalide"""
        access_token, _ = generate_tokens(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        data = {
            'refresh_token': 'invalid.token.here'
        }
        response = self.client.post(self.refresh_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('invalide', response.data['message'])
    
    def test_logout(self):
        """Test de déconnexion"""
        access_token, _ = generate_tokens(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        response = self.client.post(self.logout_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Déconnexion réussie')
    
    def test_profile_success(self):
        """Test de récupération du profil avec authentification"""
        access_token, _ = generate_tokens(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user', response.data)
        user_data = response.data['user']
        self.assertEqual(user_data['username'], self.user.username)
        self.assertEqual(user_data['email'], self.user.email)
        self.assertEqual(user_data['first_name'], self.user.first_name)
        self.assertEqual(user_data['last_name'], self.user.last_name)
    
    def test_profile_without_authentication(self):
        """Test de récupération du profil sans authentification"""
        response = self.client.get(self.profile_url)
        
        # Dans Django REST Framework, sans authentification c'est souvent 403
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
    
    def test_profile_with_invalid_token(self):
        """Test de récupération du profil avec token invalide"""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid.token.here')
        
        response = self.client.get(self.profile_url)
        
        # Dans Django REST Framework, token invalide peut renvoyer 403 ou 401
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])


class AuthIntegrationTestCase(APITestCase):
    """Tests d'intégration pour le flux d'authentification complet"""
    
    def setUp(self):
        """Configuration initiale pour chaque test"""
        self.client = APIClient()
        self.login_url = '/api/v1/auth/login/'
        self.register_url = '/api/v1/auth/register/'
        self.profile_url = '/api/v1/auth/profile/'
        self.refresh_url = '/api/v1/auth/refresh_token/'
    
    def test_complete_auth_flow(self):
        """Test du flux d'authentification complet : inscription -> connexion -> profil -> rafraîchissement"""
        # 1. Inscription
        register_data = {
            'username': 'flowtest@example.com',
            'email': 'flowtest@example.com',
            'password': 'flowpassword123'
        }
        register_response = self.client.post(self.register_url, register_data, format='json')
        self.assertEqual(register_response.status_code, status.HTTP_201_CREATED)
        
        # 2. Connexion
        login_data = {
            'username': 'flowtest@example.com',
            'password': 'flowpassword123'
        }
        login_response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        
        access_token = login_response.data['access_token']
        refresh_token = login_response.data['refresh_token']
        
        # 3. Accès au profil
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        profile_response = self.client.get(self.profile_url)
        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)
        self.assertEqual(profile_response.data['user']['username'], 'flowtest@example.com')
        
        # 4. Rafraîchissement du token
        import time
        time.sleep(0.01)  # Petit délai pour assurer unicité des timestamps
        refresh_data = {'refresh_token': refresh_token}
        refresh_response = self.client.post(self.refresh_url, refresh_data, format='json')
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        
        new_access_token = refresh_response.data['access_token']
        self.assertNotEqual(access_token, new_access_token)
        
        # 5. Utilisation du nouveau token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {new_access_token}')
        profile_response_2 = self.client.get(self.profile_url)
        self.assertEqual(profile_response_2.status_code, status.HTTP_200_OK)
