from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User

class BaseModel(models.Model):
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Account(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    solde = models.DecimalField(decimal_places=2, max_digits=20, default=Decimal(0.0))

class Operation(BaseModel):
    compte_reference = models.ForeignKey(Account, on_delete=models.CASCADE)
    montant = models.DecimalField(decimal_places=2, max_digits=20)
    description = models.CharField(max_length=255)

class DirectDebit(Operation):
    date_prelevement = models.DateField()
    echeance = models.DateField(blank=True, default=None)

    def as_echeance(self) -> bool:
        return True if self.echeance else False
    
