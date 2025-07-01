"""
Services pour la gestion des transactions automatiques
Optimise les performances en évitant les doublons et en centralisant la logique
"""

from decimal import Decimal
from datetime import date, datetime, timedelta
from django.db import transaction, models
from django.contrib.auth.models import User
from dateutil.relativedelta import relativedelta
from typing import List, Dict, Optional, Tuple
import time

from my_frais.models import (
    Account, DirectDebit, RecurringIncome, 
    AutomaticTransaction, AutomatedTask
)


class AutomaticTransactionService:
    """
    Service centralisé pour gérer les transactions automatiques
    Optimise les performances en traitant les transactions par lot
    """
    
    @classmethod
    def process_daily_transactions(cls, user: Optional[User] = None) -> Dict[str, int]:
        """
        Traite toutes les transactions automatiques du jour
        Retourne un dictionnaire avec le nombre de transactions traitées par type
        """
        start_time = time.time()
        today = date.today()
        
        # Filtrer par utilisateur si spécifié
        account_filter = {}
        if user and not user.is_staff:
            account_filter['user'] = user
        
        # Traiter les prélèvements
        payments_count = cls._process_direct_debits(today, account_filter)
        
        # Traiter les revenus
        incomes_count = cls._process_recurring_incomes(today, account_filter)
        
        total_count = payments_count + incomes_count
        execution_duration = time.time() - start_time
        
        # Enregistrer la tâche automatique
        cls._log_processing_task(
            total_count, payments_count, incomes_count, 
            execution_duration, today
        )
        
        return {
            'total': total_count,
            'payments': payments_count,
            'incomes': incomes_count,
            'execution_duration': execution_duration
        }
    
    @classmethod
    def _process_direct_debits(cls, target_date: date, account_filter: Dict) -> int:
        """Traite tous les prélèvements à échéance pour une date donnée"""
        processed_count = 0
        
        # Récupérer tous les prélèvements actifs à échéance
        due_payments = DirectDebit.objects.filter(
            actif=True,
            date_prelevement__lte=target_date
        ).exclude(
            echeance__lt=target_date
        ).select_related('compte_reference')
        
        # Filtrer par compte si nécessaire
        if account_filter:
            due_payments = due_payments.filter(compte_reference__user__in=account_filter.get('user', []))
        
        # Traiter par lot pour optimiser les performances
        for payment in due_payments:
            if cls._process_single_direct_debit(payment, target_date):
                processed_count += 1
        
        return processed_count
    
    @classmethod
    def _process_recurring_incomes(cls, target_date: date, account_filter: Dict) -> int:
        """Traite tous les revenus à échéance pour une date donnée"""
        processed_count = 0
        
        # Récupérer tous les revenus actifs à échéance
        due_incomes = RecurringIncome.objects.filter(
            actif=True,
            date_premier_versement__lte=target_date
        ).exclude(
            date_fin__lt=target_date
        ).select_related('compte_reference')
        
        # Filtrer par compte si nécessaire
        if account_filter:
            due_incomes = due_incomes.filter(compte_reference__user__in=account_filter.get('user', []))
        
        # Traiter par lot pour optimiser les performances
        for income in due_incomes:
            if cls._process_single_recurring_income(income, target_date):
                processed_count += 1
        
        return processed_count
    
    @classmethod
    def _process_single_direct_debit(cls, payment: DirectDebit, target_date: date) -> bool:
        """Traite un seul prélèvement automatique"""
        source_id = f"direct_debit_{payment.id}_{payment.date_prelevement}"
        
        # Vérifier si la transaction existe déjà
        if AutomaticTransaction.objects.filter(
            source_id=source_id, 
            transaction_type='direct_debit'
        ).exists():
            return False
        
        try:
            with transaction.atomic():
                # Double vérification dans la transaction
                if AutomaticTransaction.objects.filter(
                    source_id=source_id, 
                    transaction_type='direct_debit'
                ).exists():
                    return False
                
                # Créer la transaction automatique
                automatic_transaction = AutomaticTransaction.objects.create(
                    compte_reference=payment.compte_reference,
                    montant=-abs(payment.montant),
                    description=f"Prélèvement automatique - {payment.description}",
                    date_transaction=target_date,
                    transaction_type='direct_debit',
                    source_id=source_id,
                    source_reference=str(payment.id),
                    created_by=payment.created_by
                )
                
                # Mettre à jour le solde du compte
                payment.compte_reference.solde += automatic_transaction.montant
                payment.compte_reference.save()
                
                # Mettre à jour la date de prélèvement pour la prochaine occurrence
                next_payment_date = payment.get_next_occurrence(target_date)
                if next_payment_date:
                    DirectDebit.objects.filter(id=payment.id).update(
                        date_prelevement=next_payment_date
                    )
                
                return True
                
        except Exception as e:
            # Log l'erreur mais ne pas faire échouer le traitement des autres transactions
            print(f"Erreur lors du traitement du prélèvement {payment.id}: {e}")
            return False
    
    @classmethod
    def _process_single_recurring_income(cls, income: RecurringIncome, target_date: date) -> bool:
        """Traite un seul revenu récurrent"""
        source_id = f"recurring_income_{income.id}_{income.date_premier_versement}"
        
        # Vérifier si la transaction existe déjà
        if AutomaticTransaction.objects.filter(
            source_id=source_id, 
            transaction_type='recurring_income'
        ).exists():
            return False
        
        try:
            with transaction.atomic():
                # Double vérification dans la transaction
                if AutomaticTransaction.objects.filter(
                    source_id=source_id, 
                    transaction_type='recurring_income'
                ).exists():
                    return False
                
                # Créer la transaction automatique
                automatic_transaction = AutomaticTransaction.objects.create(
                    compte_reference=income.compte_reference,
                    montant=abs(income.montant),
                    description=f"Revenu automatique - {income.type_revenu} - {income.description}",
                    date_transaction=target_date,
                    transaction_type='recurring_income',
                    source_id=source_id,
                    source_reference=str(income.id),
                    created_by=income.created_by
                )
                
                # Mettre à jour le solde du compte
                income.compte_reference.solde += automatic_transaction.montant
                income.compte_reference.save()
                
                # Mettre à jour la date de versement pour la prochaine occurrence
                next_income_date = income.get_next_occurrence(target_date)
                if next_income_date:
                    RecurringIncome.objects.filter(id=income.id).update(
                        date_premier_versement=next_income_date
                    )
                
                return True
                
        except Exception as e:
            # Log l'erreur mais ne pas faire échouer le traitement des autres transactions
            print(f"Erreur lors du traitement du revenu {income.id}: {e}")
            return False
    
    @classmethod
    def _log_processing_task(cls, total_count: int, payments_count: int, 
                           incomes_count: int, execution_duration: float, 
                           target_date: date) -> None:
        """Enregistre la tâche de traitement automatique"""
        try:
            if total_count > 0:
                status = 'SUCCESS'
            else:
                status = 'SUCCESS'  # Aucune transaction à traiter est aussi un succès
            
            AutomatedTask.log_task(
                task_type='BOTH_PROCESSING',
                status=status,
                processed_count=total_count,
                execution_duration=execution_duration,
                details={
                    'date_execution': target_date.isoformat(),
                    'heure_execution': datetime.now().strftime('%H:%M:%S'),
                    'type_operation': 'complet',
                    'prélèvements_traités': payments_count,
                    'revenus_traités': incomes_count
                }
            )
        except Exception as e:
            print(f"Erreur lors de l'enregistrement de la tâche: {e}")
    
    @classmethod
    def get_account_balance_with_automatic_transactions(cls, account: Account, 
                                                      target_date: date = None) -> Decimal:
        """
        Calcule le solde d'un compte en incluant les transactions automatiques
        jusqu'à une date donnée
        """
        if target_date is None:
            target_date = date.today()
        
        # Solde de base du compte
        base_balance = account.solde
        
        # Ajouter les transactions automatiques futures non encore traitées
        future_transactions = AutomaticTransaction.objects.filter(
            compte_reference=account,
            date_transaction__gt=target_date,
            processed=True
        ).aggregate(
            total=models.Sum('montant')
        )['total'] or Decimal('0')
        
        return base_balance + future_transactions
    
    @classmethod
    def get_transaction_summary(cls, account: Account, 
                              start_date: date = None, 
                              end_date: date = None) -> Dict:
        """
        Retourne un résumé des transactions automatiques pour un compte
        """
        if start_date is None:
            start_date = date.today() - timedelta(days=30)
        if end_date is None:
            end_date = date.today()
        
        transactions = AutomaticTransaction.objects.filter(
            compte_reference=account,
            date_transaction__range=[start_date, end_date]
        )
        
        payments = transactions.filter(transaction_type='direct_debit')
        incomes = transactions.filter(transaction_type='recurring_income')
        
        return {
            'total_transactions': transactions.count(),
            'payments_count': payments.count(),
            'incomes_count': incomes.count(),
            'payments_total': payments.aggregate(total=models.Sum('montant'))['total'] or Decimal('0'),
            'incomes_total': incomes.aggregate(total=models.Sum('montant'))['total'] or Decimal('0'),
            'net_impact': (incomes.aggregate(total=models.Sum('montant'))['total'] or Decimal('0')) + 
                         (payments.aggregate(total=models.Sum('montant'))['total'] or Decimal('0'))
        }


class BudgetProjectionService:
    """
    Service pour calculer les projections de budget en utilisant le nouveau système
    de transactions automatiques
    """
    
    @classmethod
    def calculate_projections(cls, account: Account, start_date: date, 
                            period_months: int, include_payments: bool = True, 
                            include_incomes: bool = True) -> List[Dict]:
        """
        Calcule les projections de budget en utilisant les transactions automatiques
        """
        end_date = start_date + relativedelta(months=period_months)
        projections = []
        current_balance = account.solde
        
        # Collecter toutes les transactions futures
        future_transactions = []
        
        if include_payments:
            payments = DirectDebit.objects.filter(
                compte_reference=account,
                actif=True,
                date_prelevement__lte=end_date
            )
            
            for payment in payments:
                occurrences = payment.get_occurrences_until(end_date)
                future_transactions.extend(occurrences)
        
        if include_incomes:
            incomes = RecurringIncome.objects.filter(
                compte_reference=account,
                actif=True,
                date_premier_versement__lte=end_date
            )
            
            for income in incomes:
                occurrences = income.get_occurrences_until(end_date)
                future_transactions.extend(occurrences)
        
        # Trier toutes les transactions par date
        future_transactions.sort(key=lambda x: x['date'])
        
        # Générer les projections mensuelles
        current_date = start_date
        for month in range(period_months):
            month_start = current_date
            month_end = current_date + relativedelta(months=1) - timedelta(days=1)
            
            # Calculer les transactions du mois
            month_transactions = [
                t for t in future_transactions 
                if month_start <= t['date'] <= month_end
            ]
            
            month_total = sum(t['montant'] for t in month_transactions)
            new_balance = current_balance + month_total
            
            projections.append({
                'month': month + 1,
                'date_debut': month_start.isoformat(),
                'date_fin': month_end.isoformat(),
                'solde_debut': float(current_balance),
                'solde_fin': float(new_balance),
                'transactions_count': len(month_transactions),
                'total_transactions': float(month_total),
                'transactions': month_transactions
            })
            
            current_balance = new_balance
            current_date = month_end + timedelta(days=1)
        
        return projections 