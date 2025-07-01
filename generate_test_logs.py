#!/usr/bin/env python3
"""
Script pour générer des logs de test pour l'interface admin
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from my_frais.logging_service import app_logger
from django.contrib.auth.models import User
from django.test import RequestFactory
from datetime import datetime, timedelta
import random

def generate_test_logs():
    """Génère des logs de test variés"""
    print("🧪 Génération de logs de test pour l'interface admin")
    print("=" * 60)
    
    # Créer un utilisateur de test
    user, created = User.objects.get_or_create(
        username='test_admin',
        defaults={'email': 'admin@test.com', 'is_staff': True}
    )
    
    # Créer une requête de test
    factory = RequestFactory()
    request = factory.post('/test/', {'test': 'data'})
    request.user = user
    request.META['REMOTE_ADDR'] = '127.0.0.1'
    request.META['HTTP_USER_AGENT'] = 'TestAgent/1.0'
    
    # Générer des logs d'authentification
    print("1. Génération de logs d'authentification...")
    auth_events = [
        ('login_success', True),
        ('login_failed', False),
        ('register_success', True),
        ('logout_success', True),
        ('login_validation_failed', False),
    ]
    
    for event_type, success in auth_events:
        app_logger.log_auth_event(
            event_type=event_type,
            user=user if success else None,
            request=request,
            success=success,
            details={'test': True, 'event': event_type}
        )
        print(f"   ✅ {event_type}")
    
    # Générer des logs CRUD
    print("2. Génération de logs CRUD...")
    crud_events = [
        ('create', 'Operation'),
        ('update', 'Account'),
        ('delete', 'DirectDebit'),
        ('create', 'BudgetProjection'),
        ('update', 'Operation'),
    ]
    
    for event_type, model_name in crud_events:
        app_logger.log_crud_event(
            event_type=event_type,
            model_name=model_name,
            object_id=random.randint(1, 1000),
            user=user,
            request=request,
            old_data={'field': 'old_value'} if event_type == 'update' else None,
            new_data={'field': 'new_value', 'amount': random.randint(10, 1000)}
        )
        print(f"   ✅ {event_type} sur {model_name}")
    
    # Générer des logs d'erreurs
    print("3. Génération de logs d'erreurs...")
    error_types = [
        ValueError("Valeur invalide"),
        TypeError("Type incorrect"),
        KeyError("Clé manquante"),
        AttributeError("Attribut non trouvé"),
    ]
    
    for error in error_types:
        app_logger.log_error(
            error=error,
            user=user,
            request=request,
            context={'test': True, 'error_type': type(error).__name__}
        )
        print(f"   ✅ Erreur {type(error).__name__}")
    
    # Générer des logs d'événements métier
    print("4. Génération de logs d'événements métier...")
    business_events = [
        ('slow_request', 'performance'),
        ('admin_access_attempt', 'security'),
        ('http_error', 'error'),
        ('bulk_operation', 'business'),
        ('data_export', 'business'),
    ]
    
    for event_type, category in business_events:
        app_logger.log_business_event(
            event_type=event_type,
            category=category,
            user=user,
            request=request,
            details={'test': True, 'category': category, 'value': random.randint(1, 100)}
        )
        print(f"   ✅ {event_type} ({category})")
    
    print("\n✅ Génération terminée!")
    print(f"📊 {len(auth_events) + len(crud_events) + len(error_types) + len(business_events)} logs générés")
    print("\n🌐 Accédez à l'interface admin: http://localhost:8000/admin/mongodb-logs/")

if __name__ == "__main__":
    generate_test_logs() 