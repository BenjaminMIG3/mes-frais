#!/usr/bin/env python
"""
Script de gestion des prélèvements automatiques et revenus récurrents
Permet de traiter manuellement les prélèvements et revenus à échéance
"""

import os
import sys
import django
from datetime import date, datetime, timedelta
from decimal import Decimal

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from my_frais.models import DirectDebit, RecurringIncome, Operation, Account


def process_daily_payments():
    """Traite tous les prélèvements à échéance pour aujourd'hui"""
    print(f"🔄 Traitement des prélèvements automatiques - {date.today()}")
    print("=" * 60)
    
    try:
        processed_count = DirectDebit.process_all_due_payments()
        
        if processed_count > 0:
            print(f"✅ {processed_count} prélèvements traités avec succès")
        else:
            print("ℹ️  Aucun prélèvement à traiter aujourd'hui")
            
        return processed_count
        
    except Exception as e:
        print(f"❌ Erreur lors du traitement: {e}")
        return 0


def process_daily_incomes():
    """Traite tous les revenus à échéance pour aujourd'hui"""
    print(f"🔄 Traitement des revenus récurrents - {date.today()}")
    print("=" * 60)
    
    try:
        processed_count = RecurringIncome.process_all_due_incomes()
        
        if processed_count > 0:
            print(f"✅ {processed_count} revenus traités avec succès")
        else:
            print("ℹ️  Aucun revenu à traiter aujourd'hui")
            
        return processed_count
        
    except Exception as e:
        print(f"❌ Erreur lors du traitement: {e}")
        return 0


def process_all_daily_operations():
    """Traite tous les prélèvements et revenus à échéance"""
    print(f"🔄 Traitement complet des opérations automatiques - {date.today()}")
    print("=" * 60)
    
    payments_count = process_daily_payments()
    incomes_count = process_daily_incomes()
    
    total_count = payments_count + incomes_count
    
    if total_count > 0:
        print(f"\n🎉 Traitement terminé: {total_count} opérations au total")
    else:
        print(f"\nℹ️  Aucune opération à traiter aujourd'hui")
    
    return total_count


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
    
    total_amount = Decimal('0.00')
    
    for payment in due_payments:
        print(f"💰 {payment.description}")
        print(f"   Compte: {payment.compte_reference.nom}")
        print(f"   Montant: {payment.montant}€")
        print(f"   Date échéance: {payment.date_prelevement}")
        print(f"   Fréquence: {payment.frequence}")
        print(f"   Créé par: {payment.created_by.username}")
        print("-" * 40)
        total_amount += payment.montant
    
    print(f"💵 Montant total à prélever: {total_amount}€")


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
    
    total_amount = Decimal('0.00')
    
    for income in due_incomes:
        print(f"💰 {income.type_revenu} - {income.description}")
        print(f"   Compte: {income.compte_reference.nom}")
        print(f"   Montant: {income.montant}€")
        print(f"   Date échéance: {income.date_premier_versement}")
        print(f"   Fréquence: {income.frequence}")
        print(f"   Créé par: {income.created_by.username}")
        print("-" * 40)
        total_amount += income.montant
    
    print(f"💵 Montant total à percevoir: {total_amount}€")


def show_upcoming_payments(days=7):
    """Affiche les prélèvements à venir dans les X prochains jours"""
    today = date.today()
    future_date = today + timedelta(days=days)
    
    print(f"📅 Prélèvements à venir dans les {days} prochains jours")
    print("=" * 60)
    
    upcoming_payments = DirectDebit.objects.filter(
        actif=True,
        date_prelevement__gte=today,
        date_prelevement__lte=future_date
    ).exclude(
        echeance__lt=today
    ).select_related('compte_reference', 'created_by').order_by('date_prelevement')
    
    if not upcoming_payments:
        print(f"ℹ️  Aucun prélèvement à venir dans les {days} prochains jours")
        return
    
    total_amount = Decimal('0.00')
    
    for payment in upcoming_payments:
        days_until = (payment.date_prelevement - today).days
        print(f"📅 {payment.date_prelevement} (dans {days_until} jours)")
        print(f"   {payment.description} - {payment.montant}€")
        print(f"   Compte: {payment.compte_reference.nom}")
        print("-" * 40)
        total_amount += payment.montant
    
    print(f"💵 Montant total à prélever: {total_amount}€")


def show_upcoming_incomes(days=7):
    """Affiche les revenus à venir dans les X prochains jours"""
    today = date.today()
    future_date = today + timedelta(days=days)
    
    print(f"📅 Revenus à venir dans les {days} prochains jours")
    print("=" * 60)
    
    upcoming_incomes = RecurringIncome.objects.filter(
        actif=True,
        date_premier_versement__gte=today,
        date_premier_versement__lte=future_date
    ).exclude(
        date_fin__lt=today
    ).select_related('compte_reference', 'created_by').order_by('date_premier_versement')
    
    if not upcoming_incomes:
        print(f"ℹ️  Aucun revenu à venir dans les {days} prochains jours")
        return
    
    total_amount = Decimal('0.00')
    
    for income in upcoming_incomes:
        days_until = (income.date_premier_versement - today).days
        print(f"📅 {income.date_premier_versement} (dans {days_until} jours)")
        print(f"   {income.type_revenu} - {income.description} - {income.montant}€")
        print(f"   Compte: {income.compte_reference.nom}")
        print("-" * 40)
        total_amount += income.montant
    
    print(f"💵 Montant total à percevoir: {total_amount}€")


def show_account_balances():
    """Affiche les soldes des comptes"""
    print("🏦 Soldes des comptes")
    print("=" * 60)
    
    accounts = Account.objects.select_related('user').all()
    
    if not accounts:
        print("ℹ️  Aucun compte trouvé")
        return
    
    total_balance = Decimal('0.00')
    
    for account in accounts:
        status = "✅ Positif" if account.solde >= 0 else "❌ Négatif"
        print(f"💰 {account.nom}")
        print(f"   Propriétaire: {account.user.username}")
        print(f"   Solde: {account.solde}€ {status}")
        print("-" * 40)
        total_balance += account.solde
    
    print(f"💵 Solde total: {total_balance}€")


def main():
    """Fonction principale du script"""
    if len(sys.argv) < 2:
        print("Usage: python manage_direct_debits.py [commande]")
        print("\nCommandes disponibles:")
        print("  process-payments    - Traiter les prélèvements à échéance")
        print("  process-incomes     - Traiter les revenus à échéance")
        print("  process-all         - Traiter toutes les opérations à échéance")
        print("  due-payments        - Afficher les prélèvements à échéance")
        print("  due-incomes         - Afficher les revenus à échéance")
        print("  upcoming-payments   - Afficher les prélèvements à venir (7 jours)")
        print("  upcoming-incomes    - Afficher les revenus à venir (7 jours)")
        print("  balances            - Afficher les soldes des comptes")
        print("  all                 - Exécuter toutes les commandes")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'process-payments':
        process_daily_payments()
    elif command == 'process-incomes':
        process_daily_incomes()
    elif command == 'process-all':
        process_all_daily_operations()
    elif command == 'due-payments':
        show_due_payments()
    elif command == 'due-incomes':
        show_due_incomes()
    elif command == 'upcoming-payments':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
        show_upcoming_payments(days)
    elif command == 'upcoming-incomes':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
        show_upcoming_incomes(days)
    elif command == 'balances':
        show_account_balances()
    elif command == 'all':
        print("🔄 Exécution de toutes les commandes...\n")
        show_account_balances()
        print()
        show_due_payments()
        print()
        show_due_incomes()
        print()
        process_all_daily_operations()
        print()
        show_upcoming_payments()
        print()
        show_upcoming_incomes()
    else:
        print(f"❌ Commande inconnue: {command}")


if __name__ == '__main__':
    main() 