from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from django.db.models.signals import post_save
from django.dispatch import receiver

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

    def process_due_payments(self):
        """Traite les prélèvements à échéance et crée les opérations correspondantes"""
        today = date.today()
        
        # Vérifier si le prélèvement est actif et à échéance
        if not self.actif:
            return False
            
        if self.echeance and today > self.echeance:
            return False
        
        # Calculer la prochaine date de prélèvement
        next_payment_date = self.get_next_occurrence()
        
        # Si la date de prélèvement est aujourd'hui ou dans le passé
        if self.date_prelevement <= today:
            # Créer l'opération de prélèvement
            operation = Operation.objects.create(
                compte_reference=self.compte_reference,
                montant=-abs(self.montant),  # Négatif pour les prélèvements
                description=f"Prélèvement automatique - {self.description}",
                date_operation=today,
                created_by=self.created_by
            )
            
            # Mettre à jour le solde du compte
            self.compte_reference.solde += operation.montant
            self.compte_reference.save()
            
            # Mettre à jour la date de prélèvement pour la prochaine occurrence
            if next_payment_date:
                self.date_prelevement = next_payment_date
                self.save(update_fields=['date_prelevement'])
            
            return True
        
        return False

    @classmethod
    def process_all_due_payments(cls):
        """Traite tous les prélèvements à échéance pour tous les comptes"""
        today = date.today()
        processed_count = 0
        
        # Récupérer tous les prélèvements actifs à échéance
        due_payments = cls.objects.filter(
            actif=True,
            date_prelevement__lte=today
        ).exclude(
            echeance__lt=today
        )
        
        for payment in due_payments:
            if payment.process_due_payments():
                processed_count += 1
        
        return processed_count

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

    def process_due_income(self):
        """Traite les revenus à échéance et crée les opérations correspondantes"""
        today = date.today()
        
        # Vérifier si le revenu est actif et à échéance
        if not self.actif:
            return False
            
        if self.date_fin and today > self.date_fin:
            return False
        
        # Calculer la prochaine date de versement
        next_income_date = self.get_next_occurrence()
        
        # Si la date de versement est aujourd'hui ou dans le passé
        if self.date_premier_versement <= today:
            # Créer l'opération de revenu
            operation = Operation.objects.create(
                compte_reference=self.compte_reference,
                montant=abs(self.montant),  # Positif pour les revenus
                description=f"Revenu automatique - {self.type_revenu} - {self.description}",
                date_operation=today,
                created_by=self.created_by
            )
            
            # Mettre à jour le solde du compte
            self.compte_reference.solde += operation.montant
            self.compte_reference.save()
            
            # Mettre à jour la date de versement pour la prochaine occurrence
            if next_income_date:
                self.date_premier_versement = next_income_date
                self.save(update_fields=['date_premier_versement'])
            
            return True
        
        return False

    @classmethod
    def process_all_due_incomes(cls):
        """Traite tous les revenus à échéance pour tous les comptes"""
        today = date.today()
        processed_count = 0
        
        # Récupérer tous les revenus actifs à échéance
        due_incomes = cls.objects.filter(
            actif=True,
            date_premier_versement__lte=today
        ).exclude(
            date_fin__lt=today
        )
        
        for income in due_incomes:
            if income.process_due_income():
                processed_count += 1
        
        return processed_count

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

# Signaux pour le traitement automatique des prélèvements
@receiver(post_save, sender=DirectDebit)
def trigger_payment_processing(sender, instance, created, **kwargs):
    """
    Signal qui déclenche le traitement automatique des prélèvements
    lors de la création ou modification d'un DirectDebit
    """
    if created:
        # Pour un nouveau prélèvement, vérifier s'il doit être traité immédiatement
        if instance.date_prelevement <= date.today():
            instance.process_due_payments()
    else:
        # Pour une modification, vérifier si la date de prélèvement a changé
        if hasattr(instance, '_state') and hasattr(instance._state, 'fields_cache'):
            old_date = instance._state.fields_cache.get('date_prelevement')
            if old_date and old_date != instance.date_prelevement:
                # La date a changé, vérifier si le nouveau prélèvement doit être traité
                if instance.date_prelevement <= date.today():
                    instance.process_due_payments()

# Signaux pour le traitement automatique des revenus récurrents
@receiver(post_save, sender=RecurringIncome)
def trigger_income_processing(sender, instance, created, **kwargs):
    """
    Signal qui déclenche le traitement automatique des revenus récurrents
    lors de la création ou modification d'un RecurringIncome
    """
    if created:
        # Pour un nouveau revenu, vérifier s'il doit être traité immédiatement
        if instance.date_premier_versement <= date.today():
            instance.process_due_income()
    else:
        # Pour une modification, vérifier si la date de versement a changé
        if hasattr(instance, '_state') and hasattr(instance._state, 'fields_cache'):
            old_date = instance._state.fields_cache.get('date_premier_versement')
            if old_date and old_date != instance.date_premier_versement:
                # La date a changé, vérifier si le nouveau revenu doit être traité
                if instance.date_premier_versement <= date.today():
                    instance.process_due_income()
    
