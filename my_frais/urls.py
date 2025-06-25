from rest_framework.routers import DefaultRouter
from my_frais.viewsets import (
    AccountViewSet, OperationViewSet, DirectDebitViewSet, 
    RecurringIncomeViewSet, BudgetProjectionViewSet
)

# Création du router global pour l'application my_frais
router = DefaultRouter()

# Enregistrement des viewsets avec leurs préfixes
router.register(r'accounts', AccountViewSet, basename='account')
router.register(r'operations', OperationViewSet, basename='operation')
router.register(r'direct-debits', DirectDebitViewSet, basename='direct-debit')
router.register(r'recurring-incomes', RecurringIncomeViewSet, basename='recurring-income')
router.register(r'budget-projections', BudgetProjectionViewSet, basename='budget-projection')

# URLs de l'application
urlpatterns = router.urls 