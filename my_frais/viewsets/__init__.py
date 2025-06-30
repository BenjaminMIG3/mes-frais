from .account_viewset import AccountViewSet
from .operation_viewset import OperationViewSet
from .direct_debit_viewset import DirectDebitViewSet
from .recurring_income_viewset import RecurringIncomeViewSet
from .budget_projection_viewset import BudgetProjectionViewSet
from .automated_task_viewset import AutomatedTaskViewSet

__all__ = [
    'AccountViewSet',
    'OperationViewSet',
    'DirectDebitViewSet',
    'RecurringIncomeViewSet',
    'BudgetProjectionViewSet',
    'AutomatedTaskViewSet'
]

# Viewsets pour l'application my_frais 