#!/usr/bin/env python3
"""
Script de génération de données de test pour le projet mes-frais.
Utilise Mimesis pour créer des données réalistes et un utilisateur root.
"""

import os
import sys
import django
from datetime import datetime, timedelta, date
import random
from decimal import Decimal
import json

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User
from django.db import connection, models
from mimesis import Generic, Finance, Person, Datetime, Text
from mimesis.locales import Locale
from dateutil.relativedelta import relativedelta

from my_frais.models import Account, Operation, DirectDebit, RecurringIncome, BudgetProjection


def clear_all_tables():
    """Vide toutes les tables de la base de données"""
    print("🗑️  Vidage de toutes les tables...")
    
    # Désactiver les contraintes de clés étrangères
    with connection.cursor() as cursor:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    
    # Supprimer toutes les données
    BudgetProjection.objects.all().delete()
    RecurringIncome.objects.all().delete()
    DirectDebit.objects.all().delete()
    Operation.objects.all().delete()
    Account.objects.all().delete()
    User.objects.all().delete()
    
    # Réactiver les contraintes
    with connection.cursor() as cursor:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    
    print("✅ Toutes les tables ont été vidées")


def create_root_user():
    """Crée l'utilisateur root"""
    print("👤 Création de l'utilisateur root...")
    
    try:
        root_user = User.objects.create_user(
            username='root',
            email='root@gmail.com',
            password='root',
            first_name='Administrateur',
            last_name='Système',
            is_staff=True,
            is_superuser=True
        )
        print(f"✅ Utilisateur root créé: {root_user.username}")
        return root_user
    except Exception as e:
        print(f"❌ Erreur lors de la création de l'utilisateur root: {e}")
        return None


def create_test_users(num_users=15):
    """Crée des utilisateurs de test"""
    print(f"👥 Création de {num_users} utilisateurs de test...")
    
    person = Person(locale=Locale.FR)
    users = []
    
    for i in range(num_users):
        try:
            user = User.objects.create_user(
                username=person.username(),
                email=person.email(),
                password='password123',
                first_name=person.first_name(),
                last_name=person.last_name()
            )
            users.append(user)
        except Exception as e:
            print(f"⚠️  Erreur lors de la création de l'utilisateur {i}: {e}")
    
    print(f"✅ {len(users)} utilisateurs créés")
    return users


def create_accounts(users, num_accounts_per_user=3):
    """Crée des comptes bancaires pour les utilisateurs"""
    print(f"🏦 Création de comptes bancaires...")
    
    finance = Finance(locale=Locale.FR)
    account_names = [
        "Compte Courant", "Livret A", "Compte Épargne", "Compte Entreprise", 
        "Compte Joint", "PEL", "Compte Jeune", "Compte Premium"
    ]
    accounts = []
    
    for user in users:
        for i in range(num_accounts_per_user):
            try:
                account = Account.objects.create(
                    user=user,
                    nom=f"{random.choice(account_names)} {finance.bank()}",
                    solde=Decimal(str(random.uniform(-1000, 25000))),
                    created_by=user
                )
                accounts.append(account)
            except Exception as e:
                print(f"⚠️  Erreur lors de la création du compte {i} pour {user.username}: {e}")
    
    print(f"✅ {len(accounts)} comptes créés")
    return accounts


def create_operations(accounts, num_operations_per_account=25):
    """Crée des opérations bancaires"""
    print(f"💰 Création d'opérations bancaires...")
    
    text = Text(locale=Locale.FR)
    operations = []
    
    operation_types = [
        'Salaire', 'Achat supermarché', 'Essence', 'Restaurant', 'Pharmacie', 
        'Virement reçu', 'Prélèvement EDF', 'Retrait DAB', 'Achat en ligne',
        'Frais bancaires', 'Remboursement', 'Allocation', 'Prime', 'Loyer'
    ]
    
    for account in accounts:
        for i in range(num_operations_per_account):
            try:
                # Date aléatoire dans les 12 derniers mois
                days_ago = random.randint(0, 365)
                operation_date = datetime.now() - timedelta(days=days_ago)
                
                operation_type = random.choice(operation_types)
                description = f"{operation_type}"
                
                # Montants plus réalistes selon le type d'opération
                if operation_type in ['Salaire', 'Prime', 'Allocation']:
                    montant = Decimal(str(random.uniform(1200, 4500)))
                elif operation_type in ['Loyer']:
                    montant = Decimal(str(random.uniform(-800, -1500)))
                elif operation_type in ['Achat supermarché', 'Restaurant']:
                    montant = Decimal(str(random.uniform(-15, -120)))
                elif operation_type in ['Essence']:
                    montant = Decimal(str(random.uniform(-40, -80)))
                else:
                    montant = Decimal(str(random.uniform(-500, 1000)))
                
                operation = Operation.objects.create(
                    compte_reference=account,
                    montant=montant,
                    description=description,
                    created_by=account.user
                )
                # Mettre à jour la date d'opération manuellement
                operation.date_operation = operation_date.date()
                operation.save()
                operations.append(operation)
            except Exception as e:
                print(f"⚠️  Erreur lors de la création de l'opération {i} pour le compte {account.id}: {e}")
    
    print(f"✅ {len(operations)} opérations créées")
    return operations


def create_direct_debits(accounts, num_debits_per_account=4):
    """Crée des prélèvements automatiques"""
    print(f"📅 Création de prélèvements automatiques...")
    
    debit_types = [
        'Électricité EDF', 'Eau Veolia', 'Internet Orange', 'Téléphone SFR', 
        'Assurance Auto', 'Assurance Habitation', 'Netflix', 'Spotify',
        'Mutuelle', 'Crédit Immobilier', 'Crédit Auto'
    ]
    
    direct_debits = []
    
    for account in accounts:
        for i in range(num_debits_per_account):
            try:
                # Date de premier prélèvement dans les 30 prochains jours
                days_prelevement = random.randint(1, 30)
                date_prelevement = date.today() + timedelta(days=days_prelevement)
                
                # Échéance dans 6 à 24 mois (ou None pour illimité)
                has_echeance = random.choice([True, False])
                echeance = None
                if has_echeance:
                    months_future = random.randint(6, 24)
                    echeance = date.today() + relativedelta(months=months_future)
                
                description = random.choice(debit_types)
                
                # Montants réalistes selon le type
                if 'Crédit' in description:
                    montant = Decimal(str(random.uniform(200, 800)))
                elif 'Assurance' in description:
                    montant = Decimal(str(random.uniform(50, 200)))
                elif description in ['Netflix', 'Spotify']:
                    montant = Decimal(str(random.uniform(8, 15)))
                else:
                    montant = Decimal(str(random.uniform(30, 150)))
                
                direct_debit = DirectDebit.objects.create(
                    compte_reference=account,
                    montant=montant,
                    description=description,
                    date_prelevement=date_prelevement,
                    echeance=echeance,
                    frequence=random.choice(['Mensuel', 'Trimestriel', 'Annuel']),
                    actif=random.choice([True, True, True, False]),  # 75% actifs
                    created_by=account.user
                )
                direct_debits.append(direct_debit)
            except Exception as e:
                print(f"⚠️  Erreur lors de la création du prélèvement {i} pour le compte {account.id}: {e}")
    
    print(f"✅ {len(direct_debits)} prélèvements automatiques créés")
    return direct_debits


def create_recurring_incomes(accounts, num_incomes_per_account=2):
    """Crée des revenus récurrents"""
    print(f"💸 Création de revenus récurrents...")
    
    income_types = [
        ('Salaire', 'Salaire Net', 1800, 4500),
        ('Subvention', 'Aide CAF', 150, 600),
        ('Aide', 'RSA', 400, 600),
        ('Pension', 'Retraite', 800, 2500),
        ('Loyer', 'Loyer appartement T2', 500, 1200),
        ('Autre', 'Revenus freelance', 200, 1500)
    ]
    
    recurring_incomes = []
    
    for account in accounts:
        for i in range(num_incomes_per_account):
            try:
                income_type, base_description, min_amount, max_amount = random.choice(income_types)
                
                # Date de premier versement dans les 30 derniers jours
                days_ago = random.randint(0, 30)
                date_premier_versement = date.today() - timedelta(days=days_ago)
                
                # Date de fin optionnelle (30% des revenus ont une date de fin)
                has_date_fin = random.choice([True, False, False, False])  # 25% ont une date de fin
                date_fin = None
                if has_date_fin:
                    months_future = random.randint(6, 18)
                    date_fin = date.today() + relativedelta(months=months_future)
                
                montant = Decimal(str(random.uniform(min_amount, max_amount)))
                
                # Fréquence selon le type de revenu
                if income_type == 'Salaire':
                    frequence = 'Mensuel'
                elif income_type in ['Pension', 'Aide']:
                    frequence = random.choice(['Mensuel', 'Trimestriel'])
                else:
                    frequence = random.choice(['Mensuel', 'Trimestriel', 'Annuel'])
                
                recurring_income = RecurringIncome.objects.create(
                    compte_reference=account,
                    montant=montant,
                    description=base_description,
                    date_premier_versement=date_premier_versement,
                    date_fin=date_fin,
                    frequence=frequence,
                    actif=random.choice([True, True, True, False]),  # 75% actifs
                    type_revenu=income_type,
                    created_by=account.user
                )
                recurring_incomes.append(recurring_income)
            except Exception as e:
                print(f"⚠️  Erreur lors de la création du revenu récurrent {i} pour le compte {account.id}: {e}")
    
    print(f"✅ {len(recurring_incomes)} revenus récurrents créés")
    return recurring_incomes


def create_budget_projections(accounts, num_projections_per_account=2):
    """Crée des projections de budget"""
    print(f"📊 Création de projections de budget...")
    
    budget_projections = []
    
    for account in accounts:
        for i in range(num_projections_per_account):
            try:
                # Date de projection récente avec plus de variabilité
                days_ago = random.randint(0, 120) + i * 7  # Espacement pour éviter duplicatas
                date_projection = date.today() - timedelta(days=days_ago)
                
                # Période de projection entre 3 et 12 mois
                periode_projection = random.choice([3, 6, 12])
                
                # Génération de données de projection fictives
                projections_data = []
                current_solde = float(account.solde)
                
                for month in range(periode_projection):
                    projection_date = date_projection + relativedelta(months=month)
                    
                    # Simulation de variations mensuelles
                    revenus = random.uniform(1500, 3500)
                    depenses = random.uniform(1200, 3200)
                    variation = revenus - depenses
                    current_solde += variation
                    
                    projections_data.append({
                        'mois': projection_date.strftime('%Y-%m'),
                        'solde_prevu': round(current_solde, 2),
                        'revenus_prevus': round(revenus, 2),
                        'depenses_prevues': round(depenses, 2),
                        'variation': round(variation, 2)
                    })
                
                budget_projection = BudgetProjection.objects.create(
                    compte_reference=account,
                    date_projection=date_projection,
                    periode_projection=periode_projection,
                    solde_initial=account.solde,
                    projections_data=projections_data,
                    created_by=account.user
                )
                budget_projections.append(budget_projection)
            except Exception as e:
                print(f"⚠️  Erreur lors de la création de la projection {i} pour le compte {account.id}: {e}")
    
    print(f"✅ {len(budget_projections)} projections de budget créées")
    return budget_projections


def update_account_balances():
    """Met à jour les soldes des comptes basés sur les opérations"""
    print("🔄 Mise à jour des soldes des comptes...")
    
    accounts = Account.objects.all()
    for account in accounts:
        total_operations = account.operations.aggregate(
            total=models.Sum('montant')
        )['total'] or Decimal('0')
        
        # Solde initial + opérations = solde final
        account.solde = Decimal('1000') + total_operations
        account.save()
    
    print("✅ Soldes des comptes mis à jour")


def main():
    """Fonction principale du script"""
    print("🚀 Début de la génération des données de test...")
    print("=" * 60)
    
    try:
        # 1. Vider toutes les tables
        clear_all_tables()
        
        # 2. Créer l'utilisateur root
        root_user = create_root_user()
        if not root_user:
            print("❌ Impossible de continuer sans l'utilisateur root")
            return
        
        # 3. Créer des utilisateurs de test
        test_users = create_test_users(num_users=15)
        
        # 4. Créer des comptes
        all_users = [root_user] + test_users
        accounts = create_accounts(all_users, num_accounts_per_user=3)
        
        # 5. Créer des opérations
        operations = create_operations(accounts, num_operations_per_account=25)
        
        # 6. Créer des prélèvements automatiques
        direct_debits = create_direct_debits(accounts, num_debits_per_account=4)
        
        # 7. Créer des revenus récurrents
        recurring_incomes = create_recurring_incomes(accounts, num_incomes_per_account=2)
        
        # 8. Créer des projections de budget
        budget_projections = create_budget_projections(accounts, num_projections_per_account=2)
        
        # 9. Mettre à jour les soldes
        update_account_balances()
        
        print("=" * 60)
        print("🎉 Génération des données terminée avec succès!")
        print(f"📊 Résumé:")
        print(f"   - Utilisateurs: {User.objects.count()}")
        print(f"   - Comptes: {Account.objects.count()}")
        print(f"   - Opérations: {Operation.objects.count()}")
        print(f"   - Prélèvements: {DirectDebit.objects.count()}")
        print(f"   - Revenus récurrents: {RecurringIncome.objects.count()}")
        print(f"   - Projections budget: {BudgetProjection.objects.count()}")
        print(f"\n🔑 Connexion root:")
        print(f"   - Username: root")
        print(f"   - Email: root@gmail.com")
        print(f"   - Password: root")
        print(f"\n📱 API disponible sur: http://localhost:8000/api/v1/")
        
    except Exception as e:
        print(f"❌ Erreur lors de la génération des données: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 