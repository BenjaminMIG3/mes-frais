#!/usr/bin/env python
"""
Test unifié du système de traitement automatique des opérations récurrentes
Regroupe les tests pour les prélèvements automatiques et les revenus récurrents
"""

import os
import django
from datetime import date, timedelta
from decimal import Decimal

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User
from my_frais.models import Account, DirectDebit, RecurringIncome, Operation


class TestAutomaticOperations:
    """Classe de test pour le système de traitement automatique"""
    
    def setup_method(self):
        """Configuration initiale pour chaque test"""
        # Créer un utilisateur de test
        self.user, created = User.objects.get_or_create(
            username='test_auto_ops',
            defaults={'email': 'test_auto_ops@example.com'}
        )
        if created:
            self.user.set_password('testpass123')
            self.user.save()
        
        # Créer un compte de test
        self.account, created = Account.objects.get_or_create(
            user=self.user,
            nom="Compte Test Auto Ops",
            defaults={
                'solde': Decimal('1000.00'),
                'created_by': self.user
            }
        )
        
        self.today = date.today()
        print(f"\n🧪 Test avec compte: {self.account.nom} - Solde initial: {self.account.solde}€")
    
    def teardown_method(self):
        """Nettoyage après chaque test"""
        # Supprimer toutes les opérations créées
        Operation.objects.filter(compte_reference=self.account).delete()
        # Supprimer les prélèvements et revenus
        DirectDebit.objects.filter(compte_reference=self.account).delete()
        RecurringIncome.objects.filter(compte_reference=self.account).delete()
        # Supprimer le compte et l'utilisateur
        self.account.delete()
        self.user.delete()
    
    def test_automatic_payment_processing(self):
        """Test du traitement automatique des prélèvements"""
        print("📋 Test du traitement automatique des prélèvements")
        print("-" * 50)
        
        # Solde initial
        solde_initial = self.account.solde
        print(f"💰 Solde initial: {solde_initial}€")
        
        # Créer un prélèvement automatique pour aujourd'hui
        direct_debit = DirectDebit.objects.create(
            compte_reference=self.account,
            montant=Decimal('50.00'),
            description="Électricité EDF",
            date_prelevement=self.today,
            frequence='Mensuel',
            actif=True,
            created_by=self.user
        )
        print(f"✅ Prélèvement créé: {direct_debit.description} - {direct_debit.montant}€")
        
        # Vérifier le nombre d'opérations avant traitement
        operations_before = Operation.objects.filter(compte_reference=self.account).count()
        print(f"📊 Opérations avant traitement: {operations_before}")
        
        # Traiter le prélèvement
        print("🔄 Traitement du prélèvement...")
        processed = direct_debit.process_due_payments()
        
        if processed:
            print("✅ Prélèvement traité avec succès")
            
            # Vérifier le nombre d'opérations après traitement
            operations_after = Operation.objects.filter(compte_reference=self.account).count()
            print(f"📊 Opérations après traitement: {operations_after}")
            
            # Vérifier le solde du compte
            self.account.refresh_from_db()
            solde_final = self.account.solde
            print(f"💰 Solde final: {solde_final}€")
            print(f"📉 Variation: {solde_final - solde_initial}€")
            
            # Vérifier que l'opération a été créée
            operation = Operation.objects.filter(
                compte_reference=self.account,
                description__contains="Prélèvement automatique"
            ).first()
            
            if operation:
                print(f"✅ Opération créée: {operation.description}")
                print(f"   Montant: {operation.montant}€")
                print(f"   Date: {operation.date_operation}")
            else:
                print("❌ Aucune opération trouvée")
            
            # Vérifier la prochaine date de prélèvement
            direct_debit.refresh_from_db()
            print(f"📅 Prochaine date de prélèvement: {direct_debit.date_prelevement}")
            
        else:
            print("❌ Le prélèvement n'a pas été traité")
    
    def test_automatic_income_processing(self):
        """Test du traitement automatique des revenus récurrents"""
        print("📋 Test du traitement automatique des revenus récurrents")
        print("-" * 50)
        
        # Solde initial
        solde_initial = self.account.solde
        print(f"💰 Solde initial: {solde_initial}€")
        
        # Créer un revenu récurrent pour aujourd'hui
        recurring_income = RecurringIncome.objects.create(
            compte_reference=self.account,
            montant=Decimal('2500.00'),
            description="Salaire Net",
            date_premier_versement=self.today,
            frequence='Mensuel',
            type_revenu='Salaire',
            actif=True,
            created_by=self.user
        )
        print(f"✅ Revenu créé: {recurring_income.type_revenu} - {recurring_income.montant}€")
        
        # Vérifier le nombre d'opérations avant traitement
        operations_before = Operation.objects.filter(compte_reference=self.account).count()
        print(f"📊 Opérations avant traitement: {operations_before}")
        
        # Traiter le revenu
        print("🔄 Traitement du revenu...")
        processed = recurring_income.process_due_income()
        
        if processed:
            print("✅ Revenu traité avec succès")
            
            # Vérifier le nombre d'opérations après traitement
            operations_after = Operation.objects.filter(compte_reference=self.account).count()
            print(f"📊 Opérations après traitement: {operations_after}")
            
            # Vérifier le solde du compte
            self.account.refresh_from_db()
            solde_final = self.account.solde
            print(f"💰 Solde final: {solde_final}€")
            print(f"📈 Variation: {solde_final - solde_initial}€")
            
            # Vérifier que l'opération a été créée
            operation = Operation.objects.filter(
                compte_reference=self.account,
                description__contains="Revenu automatique"
            ).first()
            
            if operation:
                print(f"✅ Opération créée: {operation.description}")
                print(f"   Montant: {operation.montant}€")
                print(f"   Date: {operation.date_operation}")
            else:
                print("❌ Aucune opération trouvée")
            
            # Vérifier la prochaine date de versement
            recurring_income.refresh_from_db()
            print(f"📅 Prochaine date de versement: {recurring_income.date_premier_versement}")
            
        else:
            print("❌ Le revenu n'a pas été traité")
    
    def test_bulk_payment_processing(self):
        """Test du traitement en lot des prélèvements"""
        print("📋 Test du traitement en lot des prélèvements")
        print("-" * 50)
        
        # Créer plusieurs prélèvements
        prélèvements = []
        for i in range(3):
            debit = DirectDebit.objects.create(
                compte_reference=self.account,
                montant=Decimal(f'{20 + i * 10}.00'),
                description=f"Prélèvement test {i+1}",
                date_prelevement=self.today,
                frequence='Mensuel',
                actif=True,
                created_by=self.user
            )
            prélèvements.append(debit)
            print(f"✅ Prélèvement {i+1} créé: {debit.montant}€")
        
        # Solde initial
        solde_initial = self.account.solde
        print(f"💰 Solde initial: {solde_initial}€")
        
        # Traiter tous les prélèvements
        print("🔄 Traitement en lot des prélèvements...")
        processed_count = DirectDebit.process_all_due_payments()
        print(f"✅ {processed_count} prélèvements traités")
        
        # Vérifier le solde final
        self.account.refresh_from_db()
        solde_final = self.account.solde
        print(f"💰 Solde final: {solde_final}€")
        print(f"📉 Variation totale: {solde_final - solde_initial}€")
        
        # Vérifier les opérations créées
        operations = Operation.objects.filter(
            compte_reference=self.account,
            description__contains="Prélèvement automatique"
        )
        print(f"📊 Opérations créées: {operations.count()}")
    
    def test_bulk_income_processing(self):
        """Test du traitement en lot des revenus récurrents"""
        print("📋 Test du traitement en lot des revenus récurrents")
        print("-" * 50)
        
        # Créer plusieurs revenus
        revenus = []
        revenu_types = ['Salaire', 'Subvention', 'Aide']
        for i in range(3):
            revenu = RecurringIncome.objects.create(
                compte_reference=self.account,
                montant=Decimal(f'{1000 + i * 500}.00'),
                description=f"Revenu test {i+1}",
                date_premier_versement=self.today,
                frequence='Mensuel',
                type_revenu=revenu_types[i],
                actif=True,
                created_by=self.user
            )
            revenus.append(revenu)
            print(f"✅ Revenu {i+1} créé: {revenu.montant}€ ({revenu.type_revenu})")
        
        # Solde initial
        solde_initial = self.account.solde
        print(f"💰 Solde initial: {solde_initial}€")
        
        # Traiter tous les revenus
        print("🔄 Traitement en lot des revenus...")
        processed_count = RecurringIncome.process_all_due_incomes()
        print(f"✅ {processed_count} revenus traités")
        
        # Vérifier le solde final
        self.account.refresh_from_db()
        solde_final = self.account.solde
        print(f"💰 Solde final: {solde_final}€")
        print(f"📈 Variation totale: {solde_final - solde_initial}€")
        
        # Vérifier les opérations créées
        operations = Operation.objects.filter(
            compte_reference=self.account,
            description__contains="Revenu automatique"
        )
        print(f"📊 Opérations créées: {operations.count()}")
    
    def test_mixed_operations(self):
        """Test du traitement mixte prélèvements + revenus"""
        print("📋 Test du traitement mixte prélèvements + revenus")
        print("-" * 50)
        
        # Solde initial
        solde_initial = self.account.solde
        print(f"💰 Solde initial: {solde_initial}€")
        
        # Créer un revenu et un prélèvement pour aujourd'hui
        revenu = RecurringIncome.objects.create(
            compte_reference=self.account,
            montant=Decimal('3000.00'),
            description="Salaire Principal",
            date_premier_versement=self.today,
            frequence='Mensuel',
            type_revenu='Salaire',
            actif=True,
            created_by=self.user
        )
        
        prelevement = DirectDebit.objects.create(
            compte_reference=self.account,
            montant=Decimal('500.00'),
            description="Loyer",
            date_prelevement=self.today,
            frequence='Mensuel',
            actif=True,
            created_by=self.user
        )
        
        print(f"✅ Revenu créé: {revenu.montant}€")
        print(f"✅ Prélèvement créé: {prelevement.montant}€")
        
        # Traiter les revenus
        print("🔄 Traitement des revenus...")
        revenus_processed = RecurringIncome.process_all_due_incomes()
        print(f"✅ {revenus_processed} revenus traités")
        
        # Traiter les prélèvements
        print("🔄 Traitement des prélèvements...")
        prelevements_processed = DirectDebit.process_all_due_payments()
        print(f"✅ {prelevements_processed} prélèvements traités")
        
        # Vérifier le solde final
        self.account.refresh_from_db()
        solde_final = self.account.solde
        print(f"💰 Solde final: {solde_final}€")
        print(f"📊 Variation totale: {solde_final - solde_initial}€")
        
        # Vérifier les opérations créées
        operations = Operation.objects.filter(compte_reference=self.account)
        print(f"📊 Total opérations créées: {operations.count()}")
        
        revenu_ops = operations.filter(description__contains="Revenu automatique")
        prelevement_ops = operations.filter(description__contains="Prélèvement automatique")
        
        print(f"   - Revenus: {revenu_ops.count()}")
        print(f"   - Prélèvements: {prelevement_ops.count()}")
    
    def test_future_operations(self):
        """Test des opérations futures (ne doivent pas être traitées)"""
        print("📋 Test des opérations futures")
        print("-" * 50)
        
        # Créer un prélèvement et un revenu pour demain
        tomorrow = self.today + timedelta(days=1)
        
        future_debit = DirectDebit.objects.create(
            compte_reference=self.account,
            montant=Decimal('100.00'),
            description="Prélèvement futur",
            date_prelevement=tomorrow,
            frequence='Mensuel',
            actif=True,
            created_by=self.user
        )
        
        future_income = RecurringIncome.objects.create(
            compte_reference=self.account,
            montant=Decimal('2000.00'),
            description="Revenu futur",
            date_premier_versement=tomorrow,
            frequence='Mensuel',
            type_revenu='Salaire',
            actif=True,
            created_by=self.user
        )
        
        print(f"✅ Prélèvement futur créé: {future_debit.date_prelevement}")
        print(f"✅ Revenu futur créé: {future_income.date_premier_versement}")
        
        # Solde initial
        solde_initial = self.account.solde
        print(f"💰 Solde initial: {solde_initial}€")
        
        # Traiter les opérations (ne devrait rien traiter)
        print("🔄 Traitement des opérations...")
        revenus_processed = RecurringIncome.process_all_due_incomes()
        payments_processed = DirectDebit.process_all_due_payments()
        
        print(f"✅ {revenus_processed} revenus traités")
        print(f"✅ {payments_processed} prélèvements traités")
        
        # Vérifier que le solde n'a pas changé
        self.account.refresh_from_db()
        solde_final = self.account.solde
        print(f"💰 Solde final: {solde_final}€")
        print(f"📊 Variation: {solde_final - solde_initial}€")
        
        # Vérifier qu'aucune opération n'a été créée
        operations = Operation.objects.filter(compte_reference=self.account)
        print(f"📊 Opérations créées: {operations.count()}")
        
        if operations.count() == 0:
            print("✅ Aucune opération créée (comportement attendu)")
        else:
            print("❌ Des opérations ont été créées (comportement inattendu)")
    
    def test_inactive_operations(self):
        """Test des opérations inactives (ne doivent pas être traitées)"""
        print("📋 Test des opérations inactives")
        print("-" * 50)
        
        # Créer un prélèvement et un revenu inactifs pour aujourd'hui
        inactive_debit = DirectDebit.objects.create(
            compte_reference=self.account,
            montant=Decimal('50.00'),
            description="Prélèvement inactif",
            date_prelevement=self.today,
            frequence='Mensuel',
            actif=False,  # Inactif
            created_by=self.user
        )
        
        inactive_income = RecurringIncome.objects.create(
            compte_reference=self.account,
            montant=Decimal('1000.00'),
            description="Revenu inactif",
            date_premier_versement=self.today,
            frequence='Mensuel',
            type_revenu='Salaire',
            actif=False,  # Inactif
            created_by=self.user
        )
        
        print(f"✅ Prélèvement inactif créé: actif={inactive_debit.actif}")
        print(f"✅ Revenu inactif créé: actif={inactive_income.actif}")
        
        # Solde initial
        solde_initial = self.account.solde
        print(f"💰 Solde initial: {solde_initial}€")
        
        # Traiter les opérations (ne devrait rien traiter)
        print("🔄 Traitement des opérations...")
        revenus_processed = RecurringIncome.process_all_due_incomes()
        payments_processed = DirectDebit.process_all_due_payments()
        
        print(f"✅ {revenus_processed} revenus traités")
        print(f"✅ {payments_processed} prélèvements traités")
        
        # Vérifier que le solde n'a pas changé
        self.account.refresh_from_db()
        solde_final = self.account.solde
        print(f"💰 Solde final: {solde_final}€")
        print(f"📊 Variation: {solde_final - solde_initial}€")
        
        # Vérifier qu'aucune opération n'a été créée
        operations = Operation.objects.filter(compte_reference=self.account)
        print(f"📊 Opérations créées: {operations.count()}")
        
        if operations.count() == 0:
            print("✅ Aucune opération créée (comportement attendu)")
        else:
            print("❌ Des opérations ont été créées (comportement inattendu)")


def run_all_tests():
    """Exécute tous les tests"""
    print("🚀 Démarrage des tests unifiés du système automatique")
    print("=" * 80)
    
    test_instance = TestAutomaticOperations()
    
    # Liste des méthodes de test
    test_methods = [
        test_instance.test_automatic_payment_processing,
        test_instance.test_automatic_income_processing,
        test_instance.test_bulk_payment_processing,
        test_instance.test_bulk_income_processing,
        test_instance.test_mixed_operations,
        test_instance.test_future_operations,
        test_instance.test_inactive_operations,
    ]
    
    passed_tests = 0
    total_tests = len(test_methods)
    
    for i, test_method in enumerate(test_methods, 1):
        print(f"\n{'='*20} Test {i}/{total_tests} {'='*20}")
        try:
            test_instance.setup_method()
            test_method()
            test_instance.teardown_method()
            print(f"✅ Test {i} réussi")
            passed_tests += 1
        except Exception as e:
            print(f"❌ Test {i} échoué: {e}")
            import traceback
            traceback.print_exc()
            try:
                test_instance.teardown_method()
            except:
                pass
    
    print(f"\n{'='*80}")
    print(f"🎉 Résultats: {passed_tests}/{total_tests} tests réussis")
    
    if passed_tests == total_tests:
        print("🎊 Tous les tests sont passés avec succès !")
    else:
        print(f"⚠️  {total_tests - passed_tests} test(s) ont échoué")
    
    return passed_tests == total_tests


if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1) 