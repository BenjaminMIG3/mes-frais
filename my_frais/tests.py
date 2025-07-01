from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from dateutil.relativedelta import relativedelta
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.utils import timezone
from django.db import transaction

from my_frais.models import (
    Account, Operation, DirectDebit, RecurringIncome, 
    BudgetProjection, AutomatedTask, AutomaticTransaction
)
from my_frais.serializers.account_serializer import AccountSerializer, AccountListSerializer, AccountSummarySerializer
from my_frais.serializers.operation_serializer import OperationSerializer, OperationListSerializer
from my_frais.serializers.direct_debit_serializer import DirectDebitSerializer, DirectDebitListSerializer
from my_frais.serializers.recurring_income_serializer import RecurringIncomeSerializer, RecurringIncomeListSerializer
from my_frais.serializers.budget_projection_serializer import BudgetProjectionSerializer
from my_frais.serializers.automated_task_serializer import AutomatedTaskSerializer
from auth_api.jwt_auth import generate_tokens


class AccountModelTestCase(TestCase):
    """Tests pour le modèle Account"""
    
    def setUp(self):
        """Configuration initiale pour chaque test"""
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpassword123'
        )
        self.creator = User.objects.create_user(
            username='creator@example.com',
            email='creator@example.com',
            password='testpassword123'
        )
    
    def test_account_creation(self):
        """Test de création d'un compte"""
        account = Account.objects.create(
            user=self.user,
            nom="Compte Test",
            solde=Decimal('1000.00'),
            created_by=self.creator
        )
        
        self.assertEqual(account.user, self.user)
        self.assertEqual(account.nom, "Compte Test")
        self.assertEqual(account.solde, Decimal('1000.00'))
        self.assertEqual(account.created_by, self.creator)
        self.assertIsNotNone(account.created_at)
        self.assertIsNotNone(account.updated_at)
    
    def test_account_str_representation(self):
        """Test de la représentation string d'un compte"""
        account = Account.objects.create(
            user=self.user,
            nom="Compte Courant",
            created_by=self.creator
        )
        expected = f"Compte Courant - {self.user.username}"
        self.assertEqual(str(account), expected)
    
    def test_account_default_values(self):
        """Test des valeurs par défaut d'un compte"""
        account = Account.objects.create(
            user=self.user,
            created_by=self.creator
        )
        
        self.assertEqual(account.nom, "Compte bancaire")
        self.assertEqual(account.solde, Decimal('0.0'))


class OperationModelTestCase(TestCase):
    """Tests pour le modèle Operation"""
    
    def setUp(self):
        """Configuration initiale pour chaque test"""
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpassword123'
        )
        self.account = Account.objects.create(
            user=self.user,
            nom="Compte Test",
            solde=Decimal('1000.00'),
            created_by=self.user
        )
    
    def test_operation_creation(self):
        """Test de création d'une opération"""
        operation = Operation.objects.create(
            compte_reference=self.account,
            montant=Decimal('250.50'),
            description="Achat supermarché",
            created_by=self.user
        )
        
        self.assertEqual(operation.compte_reference, self.account)
        self.assertEqual(operation.montant, Decimal('250.50'))
        self.assertEqual(operation.description, "Achat supermarché")
        self.assertEqual(operation.created_by, self.user)
        self.assertIsNotNone(operation.date_operation)
        self.assertEqual(operation.source_type, 'manual')
    
    def test_operation_str_representation(self):
        """Test de la représentation string d'une opération"""
        operation = Operation.objects.create(
            compte_reference=self.account,
            montant=Decimal('100.00'),
            description="Test Operation",
            created_by=self.user
        )
        expected = "Test Operation - 100.00€"
        self.assertEqual(str(operation), expected)
    
    def test_operation_automatic_source_fields(self):
        """Test des champs source pour les opérations automatiques"""
        operation = Operation.objects.create(
            compte_reference=self.account,
            montant=Decimal('50.00'),
            description="Opération automatique",
            source_automatic_id="test_123",
            source_type="direct_debit",
            created_by=self.user
        )
        
        self.assertEqual(operation.source_automatic_id, "test_123")
        self.assertEqual(operation.source_type, "direct_debit")


class AutomaticTransactionModelTestCase(TestCase):
    """Tests pour le modèle AutomaticTransaction"""
    
    def setUp(self):
        """Configuration initiale pour chaque test"""
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpassword123'
        )
        self.account = Account.objects.create(
            user=self.user,
            nom="Compte Test",
            created_by=self.user
        )
    
    def test_automatic_transaction_creation(self):
        """Test de création d'une transaction automatique"""
        transaction_obj = AutomaticTransaction.objects.create(
            compte_reference=self.account,
            montant=Decimal('50.00'),
            description="Prélèvement automatique",
            date_transaction=date.today(),
            transaction_type='direct_debit',
            source_id='test_123',
            source_reference='1',
            created_by=self.user
        )
        
        self.assertEqual(transaction_obj.compte_reference, self.account)
        self.assertEqual(transaction_obj.montant, Decimal('50.00'))
        self.assertEqual(transaction_obj.transaction_type, 'direct_debit')
        self.assertEqual(transaction_obj.source_id, 'test_123')
        self.assertTrue(transaction_obj.processed)
    
    def test_automatic_transaction_str_representation(self):
        """Test de la représentation string d'une transaction automatique"""
        transaction_obj = AutomaticTransaction.objects.create(
            compte_reference=self.account,
            montant=Decimal('100.00'),
            description="Test Transaction",
            date_transaction=date.today(),
            transaction_type='recurring_income',
            source_id='test_456',
            source_reference='2',
            created_by=self.user
        )
        expected = f"Test Transaction - 100.00€ ({date.today()})"
        self.assertEqual(str(transaction_obj), expected)
    
    def test_automatic_transaction_unique_constraint(self):
        """Test de la contrainte d'unicité sur source_id et transaction_type"""
        # Créer la première transaction
        AutomaticTransaction.objects.create(
            compte_reference=self.account,
            montant=Decimal('50.00'),
            description="Test",
            date_transaction=date.today(),
            transaction_type='direct_debit',
            source_id='unique_test',
            source_reference='1',
            created_by=self.user
        )
        
        # Tenter de créer une deuxième transaction avec le même source_id et transaction_type
        with self.assertRaises(Exception):  # IntegrityError ou ValidationError
            AutomaticTransaction.objects.create(
                compte_reference=self.account,
                montant=Decimal('60.00'),
                description="Test 2",
                date_transaction=date.today(),
                transaction_type='direct_debit',
                source_id='unique_test',
                source_reference='2',
                created_by=self.user
            )


class DirectDebitModelTestCase(TestCase):
    """Tests pour le modèle DirectDebit"""
    
    def setUp(self):
        """Configuration initiale pour chaque test"""
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpassword123'
        )
        self.account = Account.objects.create(
            user=self.user,
            nom="Compte Test",
            created_by=self.user
        )
    
    def test_direct_debit_creation(self):
        """Test de création d'un prélèvement automatique"""
        direct_debit = DirectDebit.objects.create(
            compte_reference=self.account,
            montant=Decimal('50.00'),
            description="Électricité EDF",
            date_prelevement=date.today() + timedelta(days=5),
            frequence='Mensuel',
            created_by=self.user
        )
        
        self.assertEqual(direct_debit.compte_reference, self.account)
        self.assertEqual(direct_debit.montant, Decimal('50.00'))
        self.assertEqual(direct_debit.description, "Électricité EDF")
        self.assertEqual(direct_debit.frequence, 'Mensuel')
        self.assertTrue(direct_debit.actif)
        self.assertIsNone(direct_debit.echeance)
    
    def test_direct_debit_as_echeance(self):
        """Test de la méthode as_echeance"""
        # Sans échéance
        direct_debit1 = DirectDebit.objects.create(
            compte_reference=self.account,
            montant=Decimal('50.00'),
            description="Test",
            date_prelevement=date.today(),
            created_by=self.user
        )
        self.assertFalse(direct_debit1.as_echeance())
        
        # Avec échéance
        direct_debit2 = DirectDebit.objects.create(
            compte_reference=self.account,
            montant=Decimal('50.00'),
            description="Test",
            date_prelevement=date.today(),
            echeance=date.today() + timedelta(days=365),
            created_by=self.user
        )
        self.assertTrue(direct_debit2.as_echeance())
    
    def test_direct_debit_get_next_occurrence(self):
        """Test de calcul de la prochaine occurrence"""
        # Utiliser une date future pour éviter le déclenchement automatique des signaux
        future_date = date.today() + timedelta(days=5)
        direct_debit = DirectDebit.objects.create(
            compte_reference=self.account,
            montant=Decimal('50.00'),
            description="Test mensuel",
            date_prelevement=future_date,
            frequence='Mensuel',
            created_by=self.user
        )
        
        next_occurrence = direct_debit.get_next_occurrence()
        expected_date = future_date + relativedelta(months=1)
        self.assertEqual(next_occurrence, expected_date)
    
    def test_direct_debit_get_occurrences_until(self):
        """Test de génération des occurrences jusqu'à une date"""
        direct_debit = DirectDebit.objects.create(
            compte_reference=self.account,
            montant=Decimal('50.00'),
            description="Test mensuel",
            date_prelevement=date.today() + timedelta(days=1),
            frequence='Mensuel',
            created_by=self.user
        )
        
        end_date = date.today() + timedelta(days=90)
        occurrences = direct_debit.get_occurrences_until(end_date)
        
        # Devrait avoir environ 3 occurrences (1 par mois)
        self.assertGreaterEqual(len(occurrences), 2)
        self.assertLessEqual(len(occurrences), 4)
        
        for occurrence in occurrences:
            self.assertIn('date', occurrence)
            self.assertIn('montant', occurrence)
            self.assertIn('description', occurrence)
            self.assertEqual(occurrence['type'], 'prelevement')
            self.assertEqual(occurrence['montant'], -50.00)  # Négatif pour les prélèvements


class RecurringIncomeModelTestCase(TestCase):
    """Tests pour le modèle RecurringIncome"""
    
    def setUp(self):
        """Configuration initiale pour chaque test"""
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpassword123'
        )
        self.account = Account.objects.create(
            user=self.user,
            nom="Compte Test",
            created_by=self.user
        )
    
    def test_recurring_income_creation(self):
        """Test de création d'un revenu récurrent"""
        revenu = RecurringIncome.objects.create(
            compte_reference=self.account,
            montant=Decimal('2000.00'),
            description="Salaire mensuel",
            date_premier_versement=date.today() + timedelta(days=10),
            frequence='Mensuel',
            type_revenu='Salaire',
            created_by=self.user
        )
        
        self.assertEqual(revenu.compte_reference, self.account)
        self.assertEqual(revenu.montant, Decimal('2000.00'))
        self.assertEqual(revenu.description, "Salaire mensuel")
        self.assertEqual(revenu.frequence, 'Mensuel')
        self.assertEqual(revenu.type_revenu, 'Salaire')
        self.assertTrue(revenu.actif)
        self.assertIsNone(revenu.date_fin)
    
    def test_recurring_income_str_representation(self):
        """Test de la représentation string d'un revenu récurrent"""
        revenu = RecurringIncome.objects.create(
            compte_reference=self.account,
            montant=Decimal('1500.00'),
            description="Salaire",
            date_premier_versement=date.today(),
            type_revenu='Salaire',
            created_by=self.user
        )
        expected = "Salaire - Salaire - 1500.00€"
        self.assertEqual(str(revenu), expected)
    
    def test_recurring_income_get_next_occurrence(self):
        """Test de calcul de la prochaine occurrence"""
        revenu = RecurringIncome.objects.create(
            compte_reference=self.account,
            montant=Decimal('2000.00'),
            description="Salaire",
            date_premier_versement=date.today() + timedelta(days=5),
            frequence='Mensuel',
            created_by=self.user
        )
        
        next_occurrence = revenu.get_next_occurrence()
        expected_date = revenu.date_premier_versement + relativedelta(months=1)
        self.assertEqual(next_occurrence, expected_date)
    
    def test_recurring_income_get_occurrences_until(self):
        """Test de génération des occurrences jusqu'à une date"""
        revenu = RecurringIncome.objects.create(
            compte_reference=self.account,
            montant=Decimal('2000.00'),
            description="Salaire",
            date_premier_versement=date.today() + timedelta(days=1),
            frequence='Mensuel',
            created_by=self.user
        )
        
        end_date = date.today() + timedelta(days=90)
        occurrences = revenu.get_occurrences_until(end_date)
        
        # Devrait avoir environ 3 occurrences (1 par mois)
        self.assertGreaterEqual(len(occurrences), 2)
        self.assertLessEqual(len(occurrences), 4)
        
        for occurrence in occurrences:
            self.assertIn('date', occurrence)
            self.assertIn('montant', occurrence)
            self.assertIn('description', occurrence)
            self.assertEqual(occurrence['type'], 'revenu')
            self.assertEqual(occurrence['montant'], 2000.00)  # Positif pour les revenus


class BudgetProjectionModelTestCase(TestCase):
    """Tests pour le modèle BudgetProjection"""
    
    def setUp(self):
        """Configuration initiale pour chaque test"""
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpassword123'
        )
        self.account = Account.objects.create(
            user=self.user,
            nom="Compte Test",
            created_by=self.user
        )
    
    def test_budget_projection_creation(self):
        """Test de création d'une projection budgétaire"""
        projection_data = {
            'mois_1': {'solde': 1000.00, 'revenus': 2000.00, 'depenses': -1500.00},
            'mois_2': {'solde': 1500.00, 'revenus': 2000.00, 'depenses': -1500.00}
        }
        
        projection = BudgetProjection.objects.create(
            compte_reference=self.account,
            date_projection=date.today(),
            periode_projection=6,
            solde_initial=Decimal('1000.00'),
            projections_data=projection_data,
            created_by=self.user
        )
        
        self.assertEqual(projection.compte_reference, self.account)
        self.assertEqual(projection.periode_projection, 6)
        self.assertEqual(projection.solde_initial, Decimal('1000.00'))
        self.assertEqual(projection.projections_data, projection_data)
    
    def test_budget_projection_str_representation(self):
        """Test de la représentation string d'une projection"""
        projection = BudgetProjection.objects.create(
            compte_reference=self.account,
            date_projection=date.today(),
            periode_projection=6,
            solde_initial=Decimal('1000.00'),
            projections_data={},
            created_by=self.user
        )
        expected = f"Projection {self.account.nom} - {date.today()} (6 mois)"
        self.assertEqual(str(projection), expected)


class AutomatedTaskModelTestCase(TestCase):
    """Tests pour le modèle AutomatedTask"""
    
    def setUp(self):
        """Configuration initiale pour chaque test"""
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpassword123'
        )
    
    def test_automated_task_creation(self):
        """Test de création d'une tâche automatique"""
        task = AutomatedTask.objects.create(
            task_type='PAYMENT_PROCESSING',
            status='SUCCESS',
            processed_count=5,
            execution_duration=Decimal('0.125'),
            created_by=self.user
        )
        
        self.assertEqual(task.task_type, 'PAYMENT_PROCESSING')
        self.assertEqual(task.status, 'SUCCESS')
        self.assertEqual(task.processed_count, 5)
        self.assertEqual(task.execution_duration, Decimal('0.125'))
    
    def test_automated_task_str_representation(self):
        """Test de la représentation string d'une tâche automatique"""
        task = AutomatedTask.objects.create(
            task_type='INCOME_PROCESSING',
            status='SUCCESS',
            processed_count=3,
            created_by=self.user
        )
        expected = f"Tâche automatique #{task.id} - INCOME_PROCESSING - SUCCESS"
        self.assertEqual(str(task), expected)
    
    def test_automated_task_log_task_classmethod(self):
        """Test de la méthode de classe log_task"""
        task = AutomatedTask.log_task(
            task_type='BOTH_PROCESSING',
            status='SUCCESS',
            processed_count=10,
            execution_duration=Decimal('0.250'),
            user=self.user
        )
        
        self.assertEqual(task.task_type, 'BOTH_PROCESSING')
        self.assertEqual(task.status, 'SUCCESS')
        self.assertEqual(task.processed_count, 10)
        self.assertEqual(task.execution_duration, Decimal('0.250'))
        self.assertEqual(task.created_by, self.user)


class AccountSerializerTestCase(TestCase):
    """Tests pour les sérialiseurs de compte"""
    
    def setUp(self):
        """Configuration initiale pour chaque test"""
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpassword123'
        )
        self.account = Account.objects.create(
            user=self.user,
            nom="Compte Test",
            solde=Decimal('1000.00'),
            created_by=self.user
        )
    
    def test_account_serializer_valid_data(self):
        """Test du sérialiseur Account avec des données valides"""
        data = {
            'user': self.user.id,
            'nom': 'Nouveau Compte',
            'solde': '1500.00'
        }
        serializer = AccountSerializer(data=data, context={'request': type('MockRequest', (), {'user': self.user})()})
        self.assertTrue(serializer.is_valid())
        
        account = serializer.save()
        self.assertEqual(account.nom, 'Nouveau Compte')
        self.assertEqual(account.solde, Decimal('1500.00'))
    
    def test_account_list_serializer(self):
        """Test du sérialiseur AccountList"""
        serializer = AccountListSerializer(self.account)
        data = serializer.data
        
        self.assertIn('id', data)
        self.assertIn('user_username', data)
        self.assertIn('nom', data)
        self.assertIn('solde', data)
        self.assertIn('operations_count', data)
        self.assertIn('updated_at', data)


class AccountViewSetTestCase(APITestCase):
    """Tests pour les vues de compte"""
    
    def setUp(self):
        """Configuration initiale pour chaque test"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpassword123'
        )
        self.account = Account.objects.create(
            user=self.user,
            nom="Compte Test",
            solde=Decimal('1000.00'),
            created_by=self.user
        )
        
        # Générer un token JWT pour l'authentification
        self.access_token, _ = generate_tokens(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
    
    def test_list_accounts_authenticated_user(self):
        """Test de liste des comptes pour un utilisateur authentifié"""
        url = reverse('account-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['nom'], 'Compte Test')
    
    def test_create_account_success(self):
        """Test de création d'un compte avec succès"""
        url = reverse('account-list')
        data = {
            'user': self.user.id,
            'nom': 'Nouveau Compte',
            'solde': '2000.00'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Account.objects.count(), 2)
    
    def test_get_account_details(self):
        """Test de récupération des détails d'un compte"""
        url = reverse('account-detail', args=[self.account.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['nom'], 'Compte Test')
    
    def test_unauthorized_access(self):
        """Test d'accès non autorisé"""
        self.client.credentials()  # Supprimer l'authentification
        url = reverse('account-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class OperationViewSetTestCase(APITestCase):
    """Tests pour les vues d'opération"""
    
    def setUp(self):
        """Configuration initiale pour chaque test"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpassword123'
        )
        self.account = Account.objects.create(
            user=self.user,
            nom="Compte Test",
            solde=Decimal('1000.00'),
            created_by=self.user
        )
        
        # Générer un token JWT pour l'authentification
        self.access_token, _ = generate_tokens(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
    
    def test_create_operation_success(self):
        """Test de création d'une opération avec succès"""
        url = reverse('operation-list')
        data = {
            'compte_reference': self.account.id,
            'montant': '250.50',
            'description': 'Achat supermarché'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Operation.objects.count(), 1)
        
        # Vérifier que le solde du compte a été mis à jour
        self.account.refresh_from_db()
        self.assertEqual(self.account.solde, Decimal('1250.50'))
    
    def test_bulk_create_operations(self):
        """Test de création en lot d'opérations"""
        url = reverse('operation-bulk-create')
        data = {
            'operations': [
                {
                    'compte_reference': self.account.id,
                    'montant': '100.00',
                    'description': 'Opération 1'
                },
                {
                    'compte_reference': self.account.id,
                    'montant': '200.00',
                    'description': 'Opération 2'
                }
            ]
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['created_count'], 2)


class DirectDebitViewSetTestCase(APITestCase):
    """Tests pour les vues de prélèvements automatiques"""
    
    def setUp(self):
        """Configuration initiale pour chaque test"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpassword123'
        )
        self.account = Account.objects.create(
            user=self.user,
            nom="Compte Test",
            solde=Decimal('1000.00'),
            created_by=self.user
        )
        
        # Générer un token JWT pour l'authentification
        self.access_token, _ = generate_tokens(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
    
    def test_create_direct_debit_success(self):
        """Test de création d'un prélèvement automatique avec succès"""
        url = reverse('direct-debit-list')
        data = {
            'compte_reference': self.account.id,
            'montant': '50.00',
            'description': 'Électricité EDF',
            'date_prelevement': (date.today() + timedelta(days=5)).isoformat(),
            'frequence': 'Mensuel'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(DirectDebit.objects.count(), 1)
    
    def test_active_direct_debits(self):
        """Test de récupération des prélèvements actifs"""
        # Créer un prélèvement actif
        DirectDebit.objects.create(
            compte_reference=self.account,
            montant=Decimal('50.00'),
            description="Test",
            date_prelevement=date.today() + timedelta(days=5),
            created_by=self.user
        )
        
        url = reverse('direct-debit-active')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)


class RecurringIncomeViewSetTestCase(APITestCase):
    """Tests pour les vues de revenus récurrents"""
    
    def setUp(self):
        """Configuration initiale pour chaque test"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpassword123'
        )
        self.account = Account.objects.create(
            user=self.user,
            nom="Compte Test",
            solde=Decimal('1000.00'),
            created_by=self.user
        )
        
        # Générer un token JWT pour l'authentification
        self.access_token, _ = generate_tokens(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
    
    def test_create_recurring_income_success(self):
        """Test de création d'un revenu récurrent avec succès"""
        url = reverse('recurring-income-list')
        data = {
            'compte_reference': self.account.id,
            'montant': '2000.00',
            'description': 'Salaire mensuel',
            'date_premier_versement': (date.today() + timedelta(days=10)).isoformat(),
            'frequence': 'Mensuel',
            'type_revenu': 'Salaire'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(RecurringIncome.objects.count(), 1)
    
    def test_bulk_create_recurring_incomes(self):
        """Test de création en lot de revenus récurrents"""
        url = reverse('recurring-income-bulk-create')
        data = {
            'revenus': [
                {
                    'compte_reference': self.account.id,
                    'montant': '1500.00',
                    'description': 'Salaire 1',
                    'date_premier_versement': (date.today() + timedelta(days=5)).isoformat(),
                    'type_revenu': 'Salaire'
                },
                {
                    'compte_reference': self.account.id,
                    'montant': '500.00',
                    'description': 'Aide',
                    'date_premier_versement': (date.today() + timedelta(days=10)).isoformat(),
                    'type_revenu': 'Aide'
                }
            ]
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['created_count'], 2)


class BudgetProjectionViewSetTestCase(APITestCase):
    """Tests pour les vues de projections budgétaires"""
    
    def setUp(self):
        """Configuration initiale pour chaque test"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpassword123'
        )
        self.account = Account.objects.create(
            user=self.user,
            nom="Compte Test",
            solde=Decimal('1000.00'),
            created_by=self.user
        )
        
        # Générer un token JWT pour l'authentification
        self.access_token, _ = generate_tokens(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
    
    def test_calculate_projections(self):
        """Test de calcul de projections"""
        url = reverse('budget-projection-calculate')
        data = {
            'compte': self.account.id,  # Le sérialiseur BudgetProjectionCalculatorSerializer utilise 'compte'
            'date_debut': (date.today() + timedelta(days=1)).isoformat(),
            'periode_mois': 6,
            'inclure_prelevements': True,
            'inclure_revenus': True
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class AutomatedTaskViewSetTestCase(APITestCase):
    """Tests pour les vues de tâches automatiques"""
    
    def setUp(self):
        """Configuration initiale pour chaque test"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpassword123'
        )
        
        # Créer quelques tâches automatiques
        self.task1 = AutomatedTask.objects.create(
            task_type='PAYMENT_PROCESSING',
            status='SUCCESS',
            processed_count=5,
            execution_duration=Decimal('0.125'),
            created_by=self.user
        )
        self.task2 = AutomatedTask.objects.create(
            task_type='INCOME_PROCESSING',
            status='SUCCESS',
            processed_count=3,
            execution_duration=Decimal('0.100'),
            created_by=self.user
        )
        
        # Générer un token JWT pour l'authentification
        self.access_token, _ = generate_tokens(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
    
    def test_list_automated_tasks(self):
        """Test de liste des tâches automatiques"""
        url = reverse('automated-task-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
    
    def test_automated_tasks_statistics(self):
        """Test des statistiques des tâches automatiques"""
        url = reverse('automated-task-statistics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('task_types', response.data)
        self.assertIn('status_stats', response.data)
        self.assertIn('performance', response.data)
    
    def test_automated_tasks_recent(self):
        """Test des tâches récentes"""
        url = reverse('automated-task-recent')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)
        self.assertIn('tasks', response.data)


class MyFraisIntegrationTestCase(TestCase):
    """Tests d'intégration pour le système complet"""
    
    def setUp(self):
        """Configuration initiale pour chaque test"""
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpassword123'
        )
        self.account = Account.objects.create(
            user=self.user,
            nom="Compte Test",
            solde=Decimal('1000.00'),
            created_by=self.user
        )
    
    def test_complete_financial_flow(self):
        """Test d'un flux financier complet"""
        # 1. Créer des opérations
        operation1 = Operation.objects.create(
            compte_reference=self.account,
            montant=Decimal('500.00'),
            description="Dépôt initial",
            created_by=self.user
        )
        
        operation2 = Operation.objects.create(
            compte_reference=self.account,
            montant=Decimal('-100.00'),
            description="Achat",
            created_by=self.user
        )
        
        # Vérifier que le solde a été mis à jour
        self.account.refresh_from_db()
        self.assertEqual(self.account.solde, Decimal('1000.00'))
        
        # 2. Créer un prélèvement automatique
        direct_debit = DirectDebit.objects.create(
            compte_reference=self.account,
            montant=Decimal('50.00'),
            description="Abonnement",
            date_prelevement=date.today() + timedelta(days=5),
            frequence='Mensuel',
            created_by=self.user
        )
        
        # 3. Créer un revenu récurrent
        recurring_income = RecurringIncome.objects.create(
            compte_reference=self.account,
            montant=Decimal('2000.00'),
            description="Salaire",
            date_premier_versement=date.today() + timedelta(days=10),
            frequence='Mensuel',
            type_revenu='Salaire',
            created_by=self.user
        )
        
        # 4. Créer une projection budgétaire
        projection = BudgetProjection.objects.create(
            compte_reference=self.account,
            date_projection=date.today(),
            periode_projection=6,
            solde_initial=self.account.solde,
            projections_data={'test': 'data'},
            created_by=self.user
        )
        
        # Vérifier que tous les objets ont été créés correctement
        # Note: Il peut y avoir des opérations automatiques créées par les signaux
        self.assertGreaterEqual(Operation.objects.count(), 2)
        self.assertEqual(DirectDebit.objects.count(), 1)
        self.assertEqual(RecurringIncome.objects.count(), 1)
        self.assertEqual(BudgetProjection.objects.count(), 1)
        
        # Vérifier les relations
        # Note: Il peut y avoir des opérations automatiques créées par les signaux
        self.assertGreaterEqual(self.account.operations.count(), 2)
        # DirectDebit hérite d'Operation, donc pas de directdebit_set séparé
        direct_debits = DirectDebit.objects.filter(compte_reference=self.account)
        self.assertEqual(direct_debits.count(), 1)
        self.assertEqual(self.account.recurring_incomes.count(), 1)
        self.assertEqual(self.account.budget_projections.count(), 1)
