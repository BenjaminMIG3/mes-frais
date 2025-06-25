from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

class BaseModel(models.Model):
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='%(class)s_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Account(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='accounts')
    nom = models.CharField(max_length=100, default="Compte bancaire")
    solde = models.DecimalField(decimal_places=2, max_digits=20, default=Decimal(0.0))

    def __str__(self):
        return f"{self.nom} - {self.user.username}"

class Operation(BaseModel):
    compte_reference = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='operations')
    montant = models.DecimalField(decimal_places=2, max_digits=20)
    description = models.CharField(max_length=255)
    date_operation = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.description} - {self.montant}€"

class DirectDebit(Operation):
    date_prelevement = models.DateField()
    echeance = models.DateField(blank=True, null=True, default=None)
    frequence = models.CharField(max_length=20, choices=[
        ('Mensuel', 'Mensuel'),
        ('Trimestriel', 'Trimestriel'),
        ('Annuel', 'Annuel')
    ], default='Mensuel')
    actif = models.BooleanField(default=True)

    def as_echeance(self) -> bool:
        return True if self.echeance else False
    
    def get_next_occurrence(self, from_date=None):
        """Calcule la prochaine occurrence du prélèvement"""
        if not from_date:
            from_date = date.today()
        
        if self.echeance and from_date >= self.echeance:
            return None
        
        current_date = max(self.date_prelevement, from_date)
        
        if self.frequence == 'Mensuel':
            return current_date + relativedelta(months=1)
        elif self.frequence == 'Trimestriel':
            return current_date + relativedelta(months=3)
        elif self.frequence == 'Annuel':
            return current_date + relativedelta(years=1)
        
        return None

    def get_occurrences_until(self, end_date):
        """Génère toutes les occurrences jusqu'à une date donnée"""
        occurrences = []
        current = self.date_prelevement
        
        while current <= end_date:
            if self.echeance and current > self.echeance:
                break
            
            if current >= date.today():
                occurrences.append({
                    'date': current,
                    'montant': -abs(self.montant),  # Négatif pour les prélèvements
                    'description': self.description,
                    'type': 'prelevement'
                })
            
            next_occurrence = self.get_next_occurrence(current)
            if not next_occurrence:
                break
            current = next_occurrence
        
        return occurrences

class RecurringIncome(BaseModel):
    """Modèle pour les revenus récurrents (salaires, subventions, aides, etc.)"""
    compte_reference = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='recurring_incomes')
    montant = models.DecimalField(decimal_places=2, max_digits=20)
    description = models.CharField(max_length=255)
    date_premier_versement = models.DateField()
    date_fin = models.DateField(blank=True, null=True, help_text="Date de fin optionnelle")
    frequence = models.CharField(max_length=20, choices=[
        ('Mensuel', 'Mensuel'),
        ('Trimestriel', 'Trimestriel'),
        ('Annuel', 'Annuel'),
        ('Hebdomadaire', 'Hebdomadaire')
    ], default='Mensuel')
    actif = models.BooleanField(default=True)
    type_revenu = models.CharField(max_length=50, choices=[
        ('Salaire', 'Salaire'),
        ('Subvention', 'Subvention'),
        ('Aide', 'Aide'),
        ('Pension', 'Pension'),
        ('Loyer', 'Loyer perçu'),
        ('Autre', 'Autre')
    ], default='Salaire')

    def __str__(self):
        return f"{self.type_revenu} - {self.description} - {self.montant}€"

    def get_next_occurrence(self, from_date=None):
        """Calcule la prochaine occurrence du revenu"""
        if not from_date:
            from_date = date.today()
        
        if self.date_fin and from_date >= self.date_fin:
            return None
        
        current_date = max(self.date_premier_versement, from_date)
        
        if self.frequence == 'Hebdomadaire':
            return current_date + timedelta(weeks=1)
        elif self.frequence == 'Mensuel':
            return current_date + relativedelta(months=1)
        elif self.frequence == 'Trimestriel':
            return current_date + relativedelta(months=3)
        elif self.frequence == 'Annuel':
            return current_date + relativedelta(years=1)
        
        return None

    def get_occurrences_until(self, end_date):
        """Génère toutes les occurrences jusqu'à une date donnée"""
        occurrences = []
        current = self.date_premier_versement
        
        while current <= end_date:
            if self.date_fin and current > self.date_fin:
                break
            
            if current >= date.today():
                occurrences.append({
                    'date': current,
                    'montant': abs(self.montant),  # Positif pour les revenus
                    'description': f"{self.type_revenu} - {self.description}",
                    'type': 'revenu'
                })
            
            next_occurrence = self.get_next_occurrence(current)
            if not next_occurrence:
                break
            current = next_occurrence
        
        return occurrences

class BudgetProjection(BaseModel):
    """Modèle pour stocker les projections de budget calculées"""
    compte_reference = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='budget_projections')
    date_projection = models.DateField()
    periode_projection = models.IntegerField(help_text="Nombre de mois à projeter")
    solde_initial = models.DecimalField(decimal_places=2, max_digits=20)
    projections_data = models.JSONField(help_text="Données des projections au format JSON")
    
    class Meta:
        unique_together = ['compte_reference', 'date_projection', 'periode_projection']
    
    def __str__(self):
        return f"Projection {self.compte_reference.nom} - {self.date_projection} ({self.periode_projection} mois)"
    
