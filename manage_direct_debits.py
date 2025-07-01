#!/usr/bin/env python
"""
Script de gestion des prélèvements automatiques et revenus récurrents
Permet de traiter manuellement les prélèvements et revenus à échéance
Utilise le nouveau système de transactions automatiques optimisé
"""

import os
import sys
import django
import time
from datetime import date, datetime, timedelta
from decimal import Decimal

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from my_frais.models import DirectDebit, RecurringIncome, Operation, Account, AutomatedTask, AutomaticTransaction
from my_frais.services import AutomaticTransactionService
from django.db import models


def process_daily_payments():
    """Traite tous les prélèvements à échéance pour aujourd'hui"""
    start_time = time.time()
    print(f"🔄 Traitement des prélèvements automatiques - {date.today()}")
    print("=" * 60)
    
    try:
        # Utiliser le nouveau service optimisé
        result = AutomaticTransactionService.process_daily_transactions()
        processed_count = result['payments']
        execution_duration = result['execution_duration']
        
        if processed_count > 0:
            print(f"✅ {processed_count} prélèvements traités avec succès")
            status = 'SUCCESS'
        else:
            print("ℹ️  Aucun prélèvement à traiter aujourd'hui")
            status = 'SUCCESS'
        
        # Enregistrer la tâche automatique
        AutomatedTask.log_task(
            task_type='PAYMENT_PROCESSING',
            status=status,
            processed_count=processed_count,
            execution_duration=execution_duration,
            details={
                'date_execution': date.today().isoformat(),
                'heure_execution': datetime.now().strftime('%H:%M:%S'),
                'type_operation': 'prélèvements',
                'systeme': 'nouveau_optimise'
            }
        )
            
        return processed_count
        
    except Exception as e:
        execution_duration = time.time() - start_time
        print(f"❌ Erreur lors du traitement: {e}")
        
        # Enregistrer la tâche en erreur
        AutomatedTask.log_task(
            task_type='PAYMENT_PROCESSING',
            status='ERROR',
            processed_count=0,
            error_message=str(e),
            execution_duration=execution_duration,
            details={
                'date_execution': date.today().isoformat(),
                'heure_execution': datetime.now().strftime('%H:%M:%S'),
                'type_operation': 'prélèvements'
            }
        )
        
        return 0


def process_daily_incomes():
    """Traite tous les revenus à échéance pour aujourd'hui"""
    start_time = time.time()
    print(f"🔄 Traitement des revenus récurrents - {date.today()}")
    print("=" * 60)
    
    try:
        # Utiliser le nouveau service optimisé
        result = AutomaticTransactionService.process_daily_transactions()
        processed_count = result['incomes']
        execution_duration = result['execution_duration']
        
        if processed_count > 0:
            print(f"✅ {processed_count} revenus traités avec succès")
            status = 'SUCCESS'
        else:
            print("ℹ️  Aucun revenu à traiter aujourd'hui")
            status = 'SUCCESS'
        
        # Enregistrer la tâche automatique
        AutomatedTask.log_task(
            task_type='INCOME_PROCESSING',
            status=status,
            processed_count=processed_count,
            execution_duration=execution_duration,
            details={
                'date_execution': date.today().isoformat(),
                'heure_execution': datetime.now().strftime('%H:%M:%S'),
                'type_operation': 'revenus',
                'systeme': 'nouveau_optimise'
            }
        )
            
        return processed_count
        
    except Exception as e:
        execution_duration = time.time() - start_time
        print(f"❌ Erreur lors du traitement: {e}")
        
        # Enregistrer la tâche en erreur
        AutomatedTask.log_task(
            task_type='INCOME_PROCESSING',
            status='ERROR',
            processed_count=0,
            error_message=str(e),
            execution_duration=execution_duration,
            details={
                'date_execution': date.today().isoformat(),
                'heure_execution': datetime.now().strftime('%H:%M:%S'),
                'type_operation': 'revenus'
            }
        )
        
        return 0


def process_all_daily_operations():
    """Traite tous les prélèvements et revenus à échéance"""
    start_time = time.time()
    print(f"🔄 Traitement complet des opérations automatiques - {date.today()}")
    print("=" * 60)
    
    try:
        # Utiliser le nouveau service optimisé
        result = AutomaticTransactionService.process_daily_transactions()
        total_count = result['total']
        payments_count = result['payments']
        incomes_count = result['incomes']
        execution_duration = result['execution_duration']
        
        if total_count > 0:
            print(f"\n🎉 Traitement terminé: {total_count} opérations au total")
            print(f"   - Prélèvements: {payments_count}")
            print(f"   - Revenus: {incomes_count}")
            status = 'SUCCESS'
        else:
            print(f"\nℹ️  Aucune opération à traiter aujourd'hui")
            status = 'SUCCESS'
        
        # Enregistrer la tâche automatique complète
        AutomatedTask.log_task(
            task_type='BOTH_PROCESSING',
            status=status,
            processed_count=total_count,
            execution_duration=execution_duration,
            details={
                'date_execution': date.today().isoformat(),
                'heure_execution': datetime.now().strftime('%H:%M:%S'),
                'type_operation': 'complet',
                'prélèvements_traités': payments_count,
                'revenus_traités': incomes_count,
                'systeme': 'nouveau_optimise'
            }
        )
        
        return total_count
        
    except Exception as e:
        execution_duration = time.time() - start_time
        print(f"❌ Erreur lors du traitement complet: {e}")
        
        # Enregistrer la tâche en erreur
        AutomatedTask.log_task(
            task_type='BOTH_PROCESSING',
            status='ERROR',
            processed_count=0,
            error_message=str(e),
            execution_duration=execution_duration,
            details={
                'date_execution': date.today().isoformat(),
                'heure_execution': datetime.now().strftime('%H:%M:%S'),
                'type_operation': 'complet'
            }
        )
        
        return 0


def show_due_payments():
    """Affiche les prélèvements à échéance"""
    today = date.today()
    
    print(f"📋 Prélèvements à échéance - {today}")
    print("=" * 60)
    
    due_payments = DirectDebit.objects.filter(
        actif=True,
        date_prelevement__lte=today
    ).exclude(
        echeance__lt=today
    ).select_related('compte_reference', 'created_by')
    
    if not due_payments:
        print("ℹ️  Aucun prélèvement à échéance")
        return
    
    print(f"📊 {due_payments.count()} prélèvements à traiter:")
    print()
    
    for payment in due_payments:
        # Vérifier si déjà traité
        source_id = f"direct_debit_{payment.id}_{payment.date_prelevement}"
        already_processed = AutomaticTransaction.objects.filter(
            source_id=source_id,
            transaction_type='direct_debit'
        ).exists()
        
        status_icon = "✅" if already_processed else "⏳"
        print(f"{status_icon} {payment.description}")
        print(f"   - Compte: {payment.compte_reference.nom}")
        print(f"   - Montant: {payment.montant}€")
        print(f"   - Date: {payment.date_prelevement}")
        print(f"   - Fréquence: {payment.frequence}")
        if already_processed:
            print(f"   - Statut: Traité")
        else:
            print(f"   - Statut: En attente")
        print()


def show_due_incomes():
    """Affiche les revenus à échéance"""
    today = date.today()
    
    print(f"📋 Revenus à échéance - {today}")
    print("=" * 60)
    
    due_incomes = RecurringIncome.objects.filter(
        actif=True,
        date_premier_versement__lte=today
    ).exclude(
        date_fin__lt=today
    ).select_related('compte_reference', 'created_by')
    
    if not due_incomes:
        print("ℹ️  Aucun revenu à échéance")
        return
    
    print(f"📊 {due_incomes.count()} revenus à traiter:")
    print()
    
    for income in due_incomes:
        # Vérifier si déjà traité
        source_id = f"recurring_income_{income.id}_{income.date_premier_versement}"
        already_processed = AutomaticTransaction.objects.filter(
            source_id=source_id,
            transaction_type='recurring_income'
        ).exists()
        
        status_icon = "✅" if already_processed else "⏳"
        print(f"{status_icon} {income.type_revenu} - {income.description}")
        print(f"   - Compte: {income.compte_reference.nom}")
        print(f"   - Montant: {income.montant}€")
        print(f"   - Date: {income.date_premier_versement}")
        print(f"   - Fréquence: {income.frequence}")
        if already_processed:
            print(f"   - Statut: Traité")
        else:
            print(f"   - Statut: En attente")
        print()


def show_upcoming_payments(days=7):
    """Affiche les prélèvements à venir"""
    today = date.today()
    future_date = today + timedelta(days=days)
    
    print(f"📋 Prélèvements à venir (prochains {days} jours) - {today}")
    print("=" * 60)
    
    upcoming_payments = DirectDebit.objects.filter(
        actif=True,
        date_prelevement__range=[today, future_date]
    ).exclude(
        echeance__lt=today
    ).select_related('compte_reference', 'created_by').order_by('date_prelevement')
    
    if not upcoming_payments:
        print("ℹ️  Aucun prélèvement à venir")
        return
    
    print(f"📊 {upcoming_payments.count()} prélèvements à venir:")
    print()
    
    for payment in upcoming_payments:
        days_until = (payment.date_prelevement - today).days
        print(f"📅 {payment.description}")
        print(f"   - Compte: {payment.compte_reference.nom}")
        print(f"   - Montant: {payment.montant}€")
        print(f"   - Date: {payment.date_prelevement} (dans {days_until} jours)")
        print(f"   - Fréquence: {payment.frequence}")
        print()


def show_upcoming_incomes(days=7):
    """Affiche les revenus à venir"""
    today = date.today()
    future_date = today + timedelta(days=days)
    
    print(f"📋 Revenus à venir (prochains {days} jours) - {today}")
    print("=" * 60)
    
    upcoming_incomes = RecurringIncome.objects.filter(
        actif=True,
        date_premier_versement__range=[today, future_date]
    ).exclude(
        date_fin__lt=today
    ).select_related('compte_reference', 'created_by').order_by('date_premier_versement')
    
    if not upcoming_incomes:
        print("ℹ️  Aucun revenu à venir")
        return
    
    print(f"📊 {upcoming_incomes.count()} revenus à venir:")
    print()
    
    for income in upcoming_incomes:
        days_until = (income.date_premier_versement - today).days
        print(f"📅 {income.type_revenu} - {income.description}")
        print(f"   - Compte: {income.compte_reference.nom}")
        print(f"   - Montant: {income.montant}€")
        print(f"   - Date: {income.date_premier_versement} (dans {days_until} jours)")
        print(f"   - Fréquence: {income.frequence}")
        print()


def show_account_balances():
    """Affiche les soldes des comptes"""
    print(f"💰 Soldes des comptes - {date.today()}")
    print("=" * 60)
    
    accounts = Account.objects.select_related('user').order_by('user__username', 'nom')
    
    if not accounts:
        print("ℹ️  Aucun compte trouvé")
        return
    
    for account in accounts:
        # Calculer le solde avec les transactions automatiques
        balance_with_automatic = AutomaticTransactionService.get_account_balance_with_automatic_transactions(account)
        
        print(f"🏦 {account.nom} ({account.user.username})")
        print(f"   - Solde actuel: {account.solde}€")
        print(f"   - Solde avec transactions automatiques: {balance_with_automatic}€")
        
        # Afficher un résumé des transactions récentes
        summary = AutomaticTransactionService.get_transaction_summary(account)
        if summary['total_transactions'] > 0:
            print(f"   - Transactions automatiques (30j): {summary['total_transactions']}")
            print(f"     • Prélèvements: {summary['payments_count']} (-{abs(summary['payments_total'])}€)")
            print(f"     • Revenus: {summary['incomes_count']} (+{summary['incomes_total']}€)")
            print(f"     • Impact net: {summary['net_impact']}€")
        print()


def show_automatic_transactions_summary():
    """Affiche un résumé des transactions automatiques"""
    print(f"📊 Résumé des transactions automatiques - {date.today()}")
    print("=" * 60)
    
    # Statistiques globales
    total_transactions = AutomaticTransaction.objects.count()
    today_transactions = AutomaticTransaction.objects.filter(date_transaction=date.today()).count()
    
    payments_total = AutomaticTransaction.objects.filter(
        transaction_type='direct_debit'
    ).aggregate(total=models.Sum('montant'))['total'] or Decimal('0')
    
    incomes_total = AutomaticTransaction.objects.filter(
        transaction_type='recurring_income'
    ).aggregate(total=models.Sum('montant'))['total'] or Decimal('0')
    
    print(f"📈 Statistiques globales:")
    print(f"   - Total des transactions: {total_transactions}")
    print(f"   - Transactions aujourd'hui: {today_transactions}")
    print(f"   - Total des prélèvements: {abs(payments_total)}€")
    print(f"   - Total des revenus: {incomes_total}€")
    print(f"   - Impact net: {incomes_total + payments_total}€")
    
    # Transactions récentes
    print(f"\n📋 5 dernières transactions:")
    recent_transactions = AutomaticTransaction.objects.select_related(
        'compte_reference', 'created_by'
    ).order_by('-created_at')[:5]
    
    for transaction in recent_transactions:
        type_icon = "💸" if transaction.transaction_type == 'direct_debit' else "💰"
        print(f"{type_icon} {transaction.description}")
        print(f"   - Compte: {transaction.compte_reference.nom}")
        print(f"   - Montant: {transaction.montant}€")
        print(f"   - Date: {transaction.date_transaction}")
        print(f"   - Type: {transaction.get_transaction_type_display()}")
        print()


def main():
    """Fonction principale du script"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Gestion des prélèvements et revenus automatiques')
    parser.add_argument('action', choices=[
        'process-payments', 'process-incomes', 'process-all',
        'show-due-payments', 'show-due-incomes', 'show-upcoming-payments',
        'show-upcoming-incomes', 'show-balances', 'show-summary'
    ], help='Action à effectuer')
    parser.add_argument('--days', type=int, default=7, help='Nombre de jours pour les prévisions')
    
    args = parser.parse_args()
    
    if args.action == 'process-payments':
        process_daily_payments()
    elif args.action == 'process-incomes':
        process_daily_incomes()
    elif args.action == 'process-all':
        process_all_daily_operations()
    elif args.action == 'show-due-payments':
        show_due_payments()
    elif args.action == 'show-due-incomes':
        show_due_incomes()
    elif args.action == 'show-upcoming-payments':
        show_upcoming_payments(args.days)
    elif args.action == 'show-upcoming-incomes':
        show_upcoming_incomes(args.days)
    elif args.action == 'show-balances':
        show_account_balances()
    elif args.action == 'show-summary':
        show_automatic_transactions_summary()


if __name__ == '__main__':
    main() 