#!/usr/bin/env python
"""
Script de test pour vérifier le fonctionnement des signaux automatiques
"""

import os
import sys
import django
from datetime import date, datetime, timedelta
from decimal import Decimal

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from my_frais.models import DirectDebit, RecurringIncome, Operation, Account, AutomatedTask
from django.contrib.auth.models import User


def test_automatic_payment_creation():
    """Test de création automatique d'un prélèvement à échéance"""
    print("🧪 Test de création automatique d'un prélèvement à échéance")
    print("=" * 60)
    
    # Créer un utilisateur de test
    user, created = User.objects.get_or_create(
        username='test_user',
        defaults={'email': 'test@example.com'}
    )
    
    # Créer un compte de test
    account, created = Account.objects.get_or_create(
        user=user,
        nom='Compte de test',
        defaults={'solde': Decimal('1000.00'), 'created_by': user}
    )
    
    # Compter les opérations avant
    operations_before = Operation.objects.count()
    tasks_before = AutomatedTask.objects.count()
    
    print(f"📊 État initial:")
    print(f"   - Opérations: {operations_before}")
    print(f"   - Tâches automatiques: {tasks_before}")
    print(f"   - Solde du compte: {account.solde}€")
    
    # Créer un prélèvement à échéance pour aujourd'hui
    direct_debit = DirectDebit.objects.create(
        compte_reference=account,
        montant=Decimal('50.00'),
        description='Test prélèvement automatique',
        date_prelevement=date.today(),
        frequence='Mensuel',
        actif=True,
        created_by=user
    )
    
    print(f"✅ Prélèvement créé: {direct_debit.description} - {direct_debit.montant}€")
    
    # Vérifier que le traitement automatique a été déclenché
    operations_after = Operation.objects.count()
    tasks_after = AutomatedTask.objects.count()
    
    print(f"📊 État après création:")
    print(f"   - Opérations: {operations_after}")
    print(f"   - Tâches automatiques: {tasks_after}")
    print(f"   - Solde du compte: {account.solde}€")
    
    # Vérifier les résultats
    if operations_after > operations_before:
        print("✅ Traitement automatique réussi - Opération créée")
        latest_operation = Operation.objects.latest('created_at')
        print(f"   - Opération: {latest_operation.description} - {latest_operation.montant}€")
    else:
        print("❌ Aucune opération créée automatiquement")
    
    if tasks_after > tasks_before:
        print("✅ Tâche automatique enregistrée")
        latest_task = AutomatedTask.objects.latest('created_at')
        print(f"   - Tâche: {latest_task.get_task_type_display()} - {latest_task.get_status_display()}")
    else:
        print("❌ Aucune tâche automatique enregistrée")
    
    print()


def test_automatic_income_creation():
    """Test de création automatique d'un revenu à échéance"""
    print("🧪 Test de création automatique d'un revenu à échéance")
    print("=" * 60)
    
    # Créer un utilisateur de test
    user, created = User.objects.get_or_create(
        username='test_user',
        defaults={'email': 'test@example.com'}
    )
    
    # Créer un compte de test
    account, created = Account.objects.get_or_create(
        user=user,
        nom='Compte de test',
        defaults={'solde': Decimal('1000.00'), 'created_by': user}
    )
    
    # Compter les opérations avant
    operations_before = Operation.objects.count()
    tasks_before = AutomatedTask.objects.count()
    
    print(f"📊 État initial:")
    print(f"   - Opérations: {operations_before}")
    print(f"   - Tâches automatiques: {tasks_before}")
    print(f"   - Solde du compte: {account.solde}€")
    
    # Créer un revenu à échéance pour aujourd'hui
    recurring_income = RecurringIncome.objects.create(
        compte_reference=account,
        montant=Decimal('100.00'),
        description='Test revenu automatique',
        type_revenu='Salaire',
        date_premier_versement=date.today(),
        frequence='Mensuel',
        actif=True,
        created_by=user
    )
    
    print(f"✅ Revenu créé: {recurring_income.description} - {recurring_income.montant}€")
    
    # Vérifier que le traitement automatique a été déclenché
    operations_after = Operation.objects.count()
    tasks_after = AutomatedTask.objects.count()
    
    print(f"📊 État après création:")
    print(f"   - Opérations: {operations_after}")
    print(f"   - Tâches automatiques: {tasks_after}")
    print(f"   - Solde du compte: {account.solde}€")
    
    # Vérifier les résultats
    if operations_after > operations_before:
        print("✅ Traitement automatique réussi - Opération créée")
        latest_operation = Operation.objects.latest('created_at')
        print(f"   - Opération: {latest_operation.description} - {latest_operation.montant}€")
    else:
        print("❌ Aucune opération créée automatiquement")
    
    if tasks_after > tasks_before:
        print("✅ Tâche automatique enregistrée")
        latest_task = AutomatedTask.objects.latest('created_at')
        print(f"   - Tâche: {latest_task.get_task_type_display()} - {latest_task.get_status_display()}")
    else:
        print("❌ Aucune tâche automatique enregistrée")
    
    print()


def test_future_payment_creation():
    """Test de création d'un prélèvement futur (ne doit pas être traité)"""
    print("🧪 Test de création d'un prélèvement futur")
    print("=" * 60)
    
    # Créer un utilisateur de test
    user, created = User.objects.get_or_create(
        username='test_user',
        defaults={'email': 'test@example.com'}
    )
    
    # Créer un compte de test
    account, created = Account.objects.get_or_create(
        user=user,
        nom='Compte de test',
        defaults={'solde': Decimal('1000.00'), 'created_by': user}
    )
    
    # Compter les opérations avant
    operations_before = Operation.objects.count()
    tasks_before = AutomatedTask.objects.count()
    
    print(f"📊 État initial:")
    print(f"   - Opérations: {operations_before}")
    print(f"   - Tâches automatiques: {tasks_before}")
    
    # Créer un prélèvement pour demain
    future_date = date.today() + timedelta(days=1)
    direct_debit = DirectDebit.objects.create(
        compte_reference=account,
        montant=Decimal('25.00'),
        description='Test prélèvement futur',
        date_prelevement=future_date,
        frequence='Mensuel',
        actif=True,
        created_by=user
    )
    
    print(f"✅ Prélèvement futur créé: {direct_debit.description} - {direct_debit.montant}€")
    print(f"   - Date d'échéance: {direct_debit.date_prelevement}")
    
    # Vérifier qu'aucun traitement automatique n'a été déclenché
    operations_after = Operation.objects.count()
    tasks_after = AutomatedTask.objects.count()
    
    print(f"📊 État après création:")
    print(f"   - Opérations: {operations_after}")
    print(f"   - Tâches automatiques: {tasks_after}")
    
    # Vérifier les résultats
    if operations_after == operations_before:
        print("✅ Aucune opération créée (comportement attendu)")
    else:
        print("❌ Opération créée alors qu'elle ne devrait pas l'être")
    
    if tasks_after == tasks_before:
        print("✅ Aucune tâche automatique créée (comportement attendu)")
    else:
        print("❌ Tâche automatique créée alors qu'elle ne devrait pas l'être")
    
    print()


def show_automated_tasks_summary():
    """Affiche un résumé des tâches automatiques"""
    print("📋 Résumé des tâches automatiques")
    print("=" * 60)
    
    total_tasks = AutomatedTask.objects.count()
    success_tasks = AutomatedTask.objects.filter(status='SUCCESS').count()
    error_tasks = AutomatedTask.objects.filter(status='ERROR').count()
    
    print(f"📊 Statistiques générales:")
    print(f"   - Total des tâches: {total_tasks}")
    print(f"   - Tâches réussies: {success_tasks}")
    print(f"   - Tâches en erreur: {error_tasks}")
    print(f"   - Taux de succès: {(success_tasks/total_tasks*100):.1f}%" if total_tasks > 0 else "   - Taux de succès: N/A")
    
    # Tâches par type
    print(f"\n📊 Tâches par type:")
    for task_type, label in AutomatedTask.TASK_TYPES:
        count = AutomatedTask.objects.filter(task_type=task_type).count()
        if count > 0:
            print(f"   - {label}: {count}")
    
    # Dernières tâches
    print(f"\n📊 5 dernières tâches:")
    recent_tasks = AutomatedTask.objects.order_by('-execution_date')[:5]
    for task in recent_tasks:
        status_icon = "✅" if task.status == 'SUCCESS' else "❌"
        print(f"   {status_icon} {task.execution_date.strftime('%d/%m %H:%M')} - {task.get_task_type_display()} - {task.processed_count} opérations")
    
    print()


def main():
    """Fonction principale du script de test"""
    print("🚀 Tests des signaux automatiques")
    print("=" * 60)
    
    try:
        # Test 1: Prélèvement à échéance
        test_automatic_payment_creation()
        
        # Test 2: Revenu à échéance
        test_automatic_income_creation()
        
        # Test 3: Prélèvement futur
        test_future_payment_creation()
        
        # Résumé des tâches automatiques
        show_automated_tasks_summary()
        
        print("🎉 Tests terminés avec succès!")
        
    except Exception as e:
        print(f"❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main() 