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

from my_frais.models import Account, Operation, DirectDebit, RecurringIncome, BudgetProjection
from my_frais.serializers.account_serializer import AccountSerializer, AccountListSerializer, AccountSummarySerializer
from my_frais.serializers.operation_serializer import OperationSerializer, OperationListSerializer
from my_frais.serializers.direct_debit_serializer import DirectDebitSerializer
from my_frais.serializers.recurring_income_serializer import RecurringIncomeSerializer
from my_frais.serializers.budget_projection_serializer import BudgetProjectionSerializer
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
        direct_debit = DirectDebit.objects.create(
            compte_reference=self.account,
            montant=Decimal('50.00'),
            description="Test mensuel",
            date_prelevement=date.today(),
            frequence='Mensuel',
            created_by=self.user
        )
        
        next_occurrence = direct_debit.get_next_occurrence()
        expected_date = date.today() + relativedelta(months=1)
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
        
        self.assertGreater(len(occurrences), 0)
        for occurrence in occurrences:
            self.assertIn('date', occurrence)
            self.assertIn('montant', occurrence)
            self.assertIn('description', occurrence)
            self.assertIn('type', occurrence)
            self.assertEqual(occurrence['type'], 'prelevement')
            self.assertLess(occurrence['montant'], 0)  # Négatif pour prélèvements


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
        income = RecurringIncome.objects.create(
            compte_reference=self.account,
            montant=Decimal('2500.00'),
            description="Salaire Net",
            date_premier_versement=date.today(),
            frequence='Mensuel',
            type_revenu='Salaire',
            created_by=self.user
        )
        
        self.assertEqual(income.compte_reference, self.account)
        self.assertEqual(income.montant, Decimal('2500.00'))
        self.assertEqual(income.description, "Salaire Net")
        self.assertEqual(income.type_revenu, 'Salaire')
        self.assertTrue(income.actif)
    
    def test_recurring_income_str_representation(self):
        """Test de la représentation string d'un revenu récurrent"""
        income = RecurringIncome.objects.create(
            compte_reference=self.account,
            montant=Decimal('2500.00'),
            description="Salaire Net",
            date_premier_versement=date.today(),
            type_revenu='Salaire',
            created_by=self.user
        )
        expected = "Salaire - Salaire Net - 2500.00€"
        self.assertEqual(str(income), expected)
    
    def test_recurring_income_get_next_occurrence(self):
        """Test de calcul de la prochaine occurrence"""
        income = RecurringIncome.objects.create(
            compte_reference=self.account,
            montant=Decimal('2500.00'),
            description="Salaire",
            date_premier_versement=date.today(),
            frequence='Mensuel',
            created_by=self.user
        )
        
        next_occurrence = income.get_next_occurrence()
        expected_date = date.today() + relativedelta(months=1)
        self.assertEqual(next_occurrence, expected_date)
    
    def test_recurring_income_get_occurrences_until(self):
        """Test de génération des occurrences jusqu'à une date"""
        income = RecurringIncome.objects.create(
            compte_reference=self.account,
            montant=Decimal('2500.00'),
            description="Salaire",
            date_premier_versement=date.today() + timedelta(days=1),
            frequence='Mensuel',
            created_by=self.user
        )
        
        end_date = date.today() + timedelta(days=90)
        occurrences = income.get_occurrences_until(end_date)
        
        self.assertGreater(len(occurrences), 0)
        for occurrence in occurrences:
            self.assertIn('date', occurrence)
            self.assertIn('montant', occurrence)
            self.assertIn('description', occurrence)
            self.assertIn('type', occurrence)
            self.assertEqual(occurrence['type'], 'revenu')
            self.assertGreater(occurrence['montant'], 0)  # Positif pour revenus


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
            solde=Decimal('1000.00'),
            created_by=self.user
        )
    
    def test_budget_projection_creation(self):
        """Test de création d'une projection de budget"""
        projections_data = [
            {
                'mois': '2024-01',
                'solde_prevu': 1200.00,
                'revenus_prevus': 2500.00,
                'depenses_prevues': 2300.00,
                'variation': 200.00
            }
        ]
        
        projection = BudgetProjection.objects.create(
            compte_reference=self.account,
            date_projection=date.today(),
            periode_projection=6,
            solde_initial=self.account.solde,
            projections_data=projections_data,
            created_by=self.user
        )
        
        self.assertEqual(projection.compte_reference, self.account)
        self.assertEqual(projection.periode_projection, 6)
        self.assertEqual(projection.solde_initial, Decimal('1000.00'))
        self.assertEqual(projection.projections_data, projections_data)
    
    def test_budget_projection_str_representation(self):
        """Test de la représentation string d'une projection"""
        projection = BudgetProjection.objects.create(
            compte_reference=self.account,
            date_projection=date.today(),
            periode_projection=3,
            solde_initial=self.account.solde,
            projections_data=[],
            created_by=self.user
        )
        
        expected = f"Projection {self.account.nom} - {date.today()} (3 mois)"
        self.assertEqual(str(projection), expected)


class AccountSerializerTestCase(TestCase):
    """Tests pour le serializer Account"""
    
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
        """Test avec des données valides"""
        data = {
            'user': self.user.id,
            'nom': 'Nouveau Compte',
            'solde': '500.00'
        }
        
        request_mock = MagicMock()
        request_mock.user = self.user
        
        serializer = AccountSerializer(data=data, context={'request': request_mock})
        self.assertTrue(serializer.is_valid())
        
        account = serializer.save()
        self.assertEqual(account.nom, 'Nouveau Compte')
        self.assertEqual(account.solde, Decimal('500.00'))
        self.assertEqual(account.created_by, self.user)
    
    def test_account_serializer_negative_balance(self):
        """Test avec un solde négatif (doit échouer)"""
        data = {
            'user': self.user.id,
            'nom': 'Compte Test',
            'solde': '-100.00'
        }
        
        request_mock = MagicMock()
        request_mock.user = self.user
        
        serializer = AccountSerializer(data=data, context={'request': request_mock})
        self.assertFalse(serializer.is_valid())
        self.assertIn('solde', serializer.errors)
    
    def test_account_list_serializer(self):
        """Test du serializer de liste"""
        # Ajouter quelques opérations pour tester le count
        Operation.objects.create(
            compte_reference=self.account,
            montant=Decimal('100.00'),
            description="Test",
            created_by=self.user
        )
        
        serializer = AccountListSerializer(self.account)
        data = serializer.data
        
        self.assertIn('operations_count', data)
        self.assertEqual(data['operations_count'], 1)
        self.assertIn('user_username', data)
        self.assertEqual(data['user_username'], self.user.username)


class AccountViewSetTestCase(APITestCase):
    """Tests pour le ViewSet Account"""
    
    def setUp(self):
        """Configuration initiale pour chaque test"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpassword123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser@example.com',
            email='otheruser@example.com',
            password='testpassword123'
        )
        
        # Authentification
        access_token, _ = generate_tokens(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Créer des comptes de test
        self.account = Account.objects.create(
            user=self.user,
            nom="Compte Principal",
            solde=Decimal('1000.00'),
            created_by=self.user
        )
        self.other_account = Account.objects.create(
            user=self.other_user,
            nom="Autre Compte",
            solde=Decimal('500.00'),
            created_by=self.other_user
        )
        
        # URLs des endpoints
        self.accounts_url = '/api/v1/accounts/'
        self.account_detail_url = f'/api/v1/accounts/{self.account.id}/'
    
    def test_list_accounts_authenticated_user(self):
        """Test de liste des comptes pour un utilisateur authentifié"""
        response = self.client.get(self.accounts_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Vérifier la structure de données (peut être paginée ou non)
        if 'results' in response.data:
            accounts_data = response.data['results']
        else:
            accounts_data = response.data
        
        self.assertEqual(len(accounts_data), 1)  # Seulement ses comptes
        self.assertEqual(accounts_data[0]['id'], self.account.id)
    
    def test_create_account_success(self):
        """Test de création d'un compte réussie"""
        data = {
            'user': self.user.id,
            'nom': 'Nouveau Compte',
            'solde': '750.00'
        }
        response = self.client.post(self.accounts_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['nom'], 'Nouveau Compte')
        self.assertEqual(float(response.data['solde']), 750.00)
        
        # Vérifier en base
        new_account = Account.objects.get(id=response.data['id'])
        self.assertEqual(new_account.created_by, self.user)
    
    def test_create_account_invalid_data(self):
        """Test de création d'un compte avec données invalides"""
        data = {
            'user': self.user.id,
            'nom': 'Compte Test',
            'solde': '-100.00'  # Solde négatif
        }
        response = self.client.post(self.accounts_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('solde', response.data)
    
    def test_get_account_details(self):
        """Test de récupération des détails d'un compte"""
        response = self.client.get(self.account_detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.account.id)
        self.assertEqual(response.data['nom'], self.account.nom)
    
    def test_update_account(self):
        """Test de mise à jour d'un compte"""
        data = {
            'nom': 'Compte Modifié',
            'solde': '1500.00'
        }
        response = self.client.patch(self.account_detail_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['nom'], 'Compte Modifié')
        
        # Vérifier en base
        self.account.refresh_from_db()
        self.assertEqual(self.account.nom, 'Compte Modifié')
    
    def test_delete_account_without_operations(self):
        """Test de suppression d'un compte sans opérations"""
        response = self.client.delete(self.account_detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Account.objects.filter(id=self.account.id).exists())
    
    def test_delete_account_with_operations(self):
        """Test de suppression d'un compte avec opérations (doit échouer)"""
        # Ajouter une opération
        Operation.objects.create(
            compte_reference=self.account,
            montant=Decimal('100.00'),
            description="Test",
            created_by=self.user
        )
        
        response = self.client.delete(self.account_detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(Account.objects.filter(id=self.account.id).exists())
    
    def test_account_operations_action(self):
        """Test de l'action personnalisée pour récupérer les opérations"""
        # Ajouter des opérations
        Operation.objects.create(
            compte_reference=self.account,
            montant=Decimal('100.00'),
            description="Opération 1",
            created_by=self.user
        )
        Operation.objects.create(
            compte_reference=self.account,
            montant=Decimal('-50.00'),
            description="Opération 2",
            created_by=self.user
        )
        
        url = f'/api/v1/accounts/{self.account.id}/operations/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['account_id'], self.account.id)
        self.assertEqual(response.data['total_operations'], 2)
        self.assertEqual(len(response.data['operations']), 2)
    
    def test_account_statistics_action(self):
        """Test de l'action personnalisée pour les statistiques"""
        # Ajouter des données pour les statistiques
        Operation.objects.create(
            compte_reference=self.account,
            montant=Decimal('200.00'),
            description="Test",
            created_by=self.user
        )
        DirectDebit.objects.create(
            compte_reference=self.account,
            montant=Decimal('50.00'),
            description="Prélèvement",
            date_prelevement=date.today() + timedelta(days=10),
            created_by=self.user
        )
        
        url = f'/api/v1/accounts/{self.account.id}/statistics/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('statistics', response.data)
        self.assertIn('total_operations', response.data['statistics'])
        self.assertIn('total_montant_operations', response.data['statistics'])
    
    def test_adjust_balance_action(self):
        """Test de l'action d'ajustement du solde"""
        initial_balance = float(self.account.solde)
        adjustment = 250.00
        
        url = f'/api/v1/accounts/{self.account.id}/adjust_balance/'
        data = {
            'montant': str(adjustment),  # Convertir en string pour éviter les problèmes de type
            'raison': 'Test ajustement'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['ajustement'], adjustment)
        self.assertEqual(response.data['nouveau_solde'], initial_balance + adjustment)
        
        # Vérifier qu'une opération d'ajustement a été créée
        adjustment_operation = Operation.objects.filter(
            compte_reference=self.account,
            description__contains='Ajustement'
        ).first()
        self.assertIsNotNone(adjustment_operation)
        self.assertEqual(adjustment_operation.montant, Decimal(str(adjustment)))
    
    def test_summary_action(self):
        """Test de l'action de résumé des comptes"""
        url = '/api/v1/accounts/summary/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_comptes', response.data)
        self.assertIn('total_solde', response.data)
        self.assertIn('comptes_negatifs', response.data)
        self.assertIn('comptes_positifs', response.data)
        self.assertEqual(response.data['total_comptes'], 1)  # Seulement les comptes de l'utilisateur
    
    def test_unauthorized_access(self):
        """Test d'accès non autorisé"""
        self.client.credentials()  # Supprimer l'authentification
        
        response = self.client.get(self.accounts_url)
        # Django REST Framework retourne 403 pour les utilisateurs non authentifiés quand ils tentent d'accéder à des ressources protégées
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_access_other_user_account(self):
        """Test d'accès au compte d'un autre utilisateur (doit échouer)"""
        other_account_url = f'/api/v1/accounts/{self.other_account.id}/'
        response = self.client.get(other_account_url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_global_overview_action(self):
        """Test de l'action global_overview"""
        # Ajouter quelques opérations pour des tests plus complets
        Operation.objects.create(
            compte_reference=self.account,
            montant=Decimal('500.00'),
            description="Test operation 1",
            created_by=self.user
        )
        Operation.objects.create(
            compte_reference=self.account,
            montant=Decimal('-100.00'),
            description="Test operation 2",
            created_by=self.user
        )
        
        url = '/api/v1/accounts/global_overview/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('resume', response.data)
        self.assertIn('repartition', response.data)
        self.assertIn('comptes', response.data)
        self.assertIn('alertes', response.data)
        
        # Vérifier la structure du résumé
        resume = response.data['resume']
        self.assertIn('total_comptes', resume)
        self.assertIn('total_solde', resume)
        self.assertIn('solde_moyen', resume)
        self.assertIn('total_operations', resume)
        
        # Vérifier qu'il y a au moins notre compte
        self.assertGreaterEqual(resume['total_comptes'], 1)
        self.assertGreaterEqual(resume['total_operations'], 2)  # Nos 2 opérations de test
        
        # Vérifier la structure des comptes
        comptes = response.data['comptes']
        self.assertIsInstance(comptes, list)
        if len(comptes) > 0:
            compte = comptes[0]
            self.assertIn('id', compte)
            self.assertIn('nom', compte)
            self.assertIn('solde', compte)
            self.assertIn('status_niveau', compte)
            self.assertIn('total_operations', compte)


class MyFraisIntegrationTestCase(APITestCase):
    """Tests d'intégration pour l'application my_frais"""
    
    def setUp(self):
        """Configuration initiale pour chaque test"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpassword123'
        )
        
        # Authentification
        access_token, _ = generate_tokens(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
    
    def test_complete_financial_flow(self):
        """Test du flux financier complet : compte -> opérations -> prélèvements -> revenus -> projections"""
        # 1. Créer un compte
        account_data = {
            'user': self.user.id,
            'nom': 'Compte Principal',
            'solde': '2000.00'
        }
        account_response = self.client.post('/api/v1/accounts/', account_data, format='json')
        self.assertEqual(account_response.status_code, status.HTTP_201_CREATED)
        account_id = account_response.data['id']
        
        # 2. Créer des opérations
        operations_data = [
            {
                'compte_reference': account_id,
                'montant': '2500.00',
                'description': 'Salaire'
            },
            {
                'compte_reference': account_id,
                'montant': '-120.00',
                'description': 'Courses'
            },
            {
                'compte_reference': account_id,
                'montant': '-80.00',
                'description': 'Essence'
            }
        ]
        
        for op_data in operations_data:
            response = self.client.post('/api/v1/operations/', op_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 3. Créer un prélèvement automatique
        direct_debit_data = {
            'compte_reference': account_id,
            'montant': '50.00',
            'description': 'Électricité',
            'date_prelevement': (date.today() + timedelta(days=5)).isoformat(),
            'frequence': 'Mensuel'
        }
        dd_response = self.client.post('/api/v1/direct-debits/', direct_debit_data, format='json')
        self.assertEqual(dd_response.status_code, status.HTTP_201_CREATED)
        
        # 4. Créer un revenu récurrent
        income_data = {
            'compte_reference': account_id,
            'montant': '2500.00',
            'description': 'Salaire Net',
            'date_premier_versement': date.today().isoformat(),
            'frequence': 'Mensuel',
            'type_revenu': 'Salaire'
        }
        income_response = self.client.post('/api/v1/recurring-incomes/', income_data, format='json')
        self.assertEqual(income_response.status_code, status.HTTP_201_CREATED)
        
        # 5. Créer une projection de budget
        projection_data = {
            'compte_reference': account_id,
            'date_projection': date.today().isoformat(),
            'periode_projection': 6
            # On retire projections_data car elle sera calculée automatiquement
        }
        projection_response = self.client.post('/api/v1/budget-projections/', projection_data, format='json')
        self.assertEqual(projection_response.status_code, status.HTTP_201_CREATED)
        
        # 6. Vérifier les statistiques du compte
        stats_response = self.client.get(f'/api/v1/accounts/{account_id}/statistics/')
        self.assertEqual(stats_response.status_code, status.HTTP_200_OK)
        self.assertIn('statistics', stats_response.data)
        # Au moins 3 opérations créées (des opérations automatiques peuvent s'ajouter)
        self.assertGreaterEqual(stats_response.data['statistics']['total_operations'], 3)
        
        # 7. Vérifier le résumé des comptes
        summary_response = self.client.get('/api/v1/accounts/summary/')
        self.assertEqual(summary_response.status_code, status.HTTP_200_OK)
        self.assertEqual(summary_response.data['total_comptes'], 1)


class BudgetProjectionAPITestCase(TestCase):
    """Tests pour l'API des projections budgétaires"""
    
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
        self.client.force_authenticate(user=self.user)
    
    def test_dashboard_with_different_periods(self):
        """Test du dashboard avec différentes périodes de projection"""
        # Test avec 3 mois (défaut)
        response = self.client.get('/api/v1/budget-projections/dashboard/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['projections']['periode_mois'], 3)
        self.assertEqual(len(data['projections']['tendance_mois']), 3)
        
        # Test avec 6 mois
        response = self.client.get('/api/v1/budget-projections/dashboard/?periode_mois=6')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['projections']['periode_mois'], 6)
        self.assertEqual(len(data['projections']['tendance_mois']), 6)
        
        # Test avec 12 mois
        response = self.client.get('/api/v1/budget-projections/dashboard/?periode_mois=12')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['projections']['periode_mois'], 12)
        self.assertEqual(len(data['projections']['tendance_mois']), 12)
    
    def test_quick_projection_with_different_periods(self):
        """Test de la projection rapide avec différentes périodes"""
        # Test avec 3 mois
        response = self.client.post('/api/v1/budget-projections/quick_projection/', {
            'compte_id': self.account.id,
            'periode_mois': 3
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['projection']['periode_mois'], 3)
        
        # Test avec 6 mois (défaut)
        response = self.client.post('/api/v1/budget-projections/quick_projection/', {
            'compte_id': self.account.id
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['projection']['periode_mois'], 6)
        
        # Test avec 12 mois
        response = self.client.post('/api/v1/budget-projections/quick_projection/', {
            'compte_id': self.account.id,
            'periode_mois': 12
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['projection']['periode_mois'], 12)
    
    def test_compare_scenarios_with_different_periods(self):
        """Test de la comparaison de scénarios avec différentes périodes"""
        # Test avec 6 mois
        response = self.client.get(f'/api/v1/budget-projections/compare_scenarios/?compte_id={self.account.id}&periode_mois=6')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['periode_mois'], 6)
        
        # Test avec 12 mois (défaut)
        response = self.client.get(f'/api/v1/budget-projections/compare_scenarios/?compte_id={self.account.id}')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['periode_mois'], 12)
        
        # Test avec 24 mois
        response = self.client.get(f'/api/v1/budget-projections/compare_scenarios/?compte_id={self.account.id}&periode_mois=24')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['periode_mois'], 24)
    
    def test_projection_period_validation(self):
        """Test de la validation des limites de période"""
        # Test avec période trop élevée (> 60 mois)
        response = self.client.get('/api/v1/budget-projections/dashboard/?periode_mois=100')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['projections']['periode_mois'], 60)  # Limitée à 60
        
        # Test avec période trop faible (< 1 mois)
        response = self.client.get('/api/v1/budget-projections/dashboard/?periode_mois=0')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['projections']['periode_mois'], 1)  # Limitée à 1
