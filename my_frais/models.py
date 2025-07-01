from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from django.db.models.signals import post_save
from django.dispatch import receiver
import time
from django.db import transaction

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
    # Ajout d'un champ pour identifier les opérations automatiques
    source_automatic_id = models.CharField(max_length=100, blank=True, null=True, help_text="ID source pour éviter les doublons")
    source_type = models.CharField(max_length=20, blank=True, null=True, choices=[
        ('direct_debit', 'Prélèvement automatique'),
        ('recurring_income', 'Revenu récurrent'),
        ('manual', 'Opération manuelle')
    ], default='manual')

    def __str__(self):
        return f"{self.description} - {self.montant}€"

class AutomaticTransaction(BaseModel):
    """
    Modèle pour tracer les transactions automatiques sans créer d'opérations
    Permet d'éviter les doublons et de garder une trace des transactions automatiques
    """
    compte_reference = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='automatic_transactions')
    montant = models.DecimalField(decimal_places=2, max_digits=20)
    description = models.CharField(max_length=255)
    date_transaction = models.DateField()
    transaction_type = models.CharField(max_length=20, choices=[
        ('direct_debit', 'Prélèvement automatique'),
        ('recurring_income', 'Revenu récurrent'),
    ])
    source_id = models.CharField(max_length=100, help_text="ID source pour éviter les doublons")
    source_reference = models.CharField(max_length=100, help_text="Référence de la source (DirectDebit.id ou RecurringIncome.id)")
    processed = models.BooleanField(default=True, help_text="Indique si la transaction a été traitée")
    
    class Meta:
        unique_together = ['source_id', 'transaction_type']
        ordering = ['-date_transaction', '-created_at']
        verbose_name = "Transaction automatique"
        verbose_name_plural = "Transactions automatiques"
    
    def __str__(self):
        return f"{self.description} - {self.montant}€ ({self.date_transaction})"

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
        if from_date is None:
            # Si aucune date n'est fournie, utiliser la date de prélèvement actuelle
            current_date = self.date_prelevement
        else:
            # Sinon, utiliser la date la plus récente entre la date de prélèvement et from_date
            current_date = max(self.date_prelevement, from_date)
        
        if self.echeance and current_date >= self.echeance:
            return None
        
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
        """Traite les prélèvements à échéance en mettant à jour uniquement le solde du compte"""
        today = date.today()
        
        # Vérifier si le prélèvement est actif et à échéance
        if not self.actif:
            return False
            
        if self.echeance and today > self.echeance:
            return False
        
        # Si la date de prélèvement est aujourd'hui ou dans le passé
        if self.date_prelevement <= today:
            # Créer un identifiant unique pour cette occurrence
            source_id = f"direct_debit_{self.id}_{self.date_prelevement}"
            
            # Vérifier si la transaction n'existe pas déjà
            existing_transaction = AutomaticTransaction.objects.filter(
                source_id=source_id,
                transaction_type='direct_debit'
            ).first()
            
            if existing_transaction:
                # La transaction existe déjà, ne pas la retraiter
                return False
            
            # Utiliser une transaction pour éviter les conditions de course
            with transaction.atomic():
                # Double vérification dans la transaction
                if AutomaticTransaction.objects.filter(source_id=source_id, transaction_type='direct_debit').exists():
                    return False
                
                # Créer la transaction automatique
                automatic_transaction = AutomaticTransaction.objects.create(
                    compte_reference=self.compte_reference,
                    montant=-abs(self.montant),  # Négatif pour les prélèvements
                    description=f"Prélèvement automatique - {self.description}",
                    date_transaction=today,
                    transaction_type='direct_debit',
                    source_id=source_id,
                    source_reference=str(self.id),
                    created_by=self.created_by
                )
                
                # Mettre à jour le solde du compte
                self.compte_reference.solde += automatic_transaction.montant
                self.compte_reference.save()
            
            # Mettre à jour la date de prélèvement pour la prochaine occurrence
            next_payment_date = self.get_next_occurrence(today)
            if next_payment_date:
                # Utiliser update pour éviter de déclencher les signaux
                DirectDebit.objects.filter(id=self.id).update(date_prelevement=next_payment_date)
                self.date_prelevement = next_payment_date
            
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
        if from_date is None:
            current_date = self.date_premier_versement
        else:
            current_date = max(self.date_premier_versement, from_date)
        
        if self.date_fin and current_date >= self.date_fin:
            return None
        
        if self.frequence == 'Mensuel':
            return current_date + relativedelta(months=1)
        elif self.frequence == 'Trimestriel':
            return current_date + relativedelta(months=3)
        elif self.frequence == 'Annuel':
            return current_date + relativedelta(years=1)
        elif self.frequence == 'Hebdomadaire':
            return current_date + timedelta(weeks=1)
        
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
                    'description': self.description,
                    'type': 'revenu'
                })
            
            next_occurrence = self.get_next_occurrence(current)
            if not next_occurrence:
                break
            current = next_occurrence
        
        return occurrences

    def process_due_income(self):
        """Traite les revenus à échéance en mettant à jour uniquement le solde du compte"""
        today = date.today()
        
        # Vérifier si le revenu est actif et à échéance
        if not self.actif:
            return False
            
        if self.date_fin and today > self.date_fin:
            return False
        
        # Si la date de versement est aujourd'hui ou dans le passé
        if self.date_premier_versement <= today:
            # Créer un identifiant unique pour cette occurrence
            source_id = f"recurring_income_{self.id}_{self.date_premier_versement}"
            
            # Vérifier si la transaction n'existe pas déjà
            existing_transaction = AutomaticTransaction.objects.filter(
                source_id=source_id,
                transaction_type='recurring_income'
            ).first()
            
            if existing_transaction:
                # La transaction existe déjà, ne pas la retraiter
                return False
            
            # Utiliser une transaction pour éviter les conditions de course
            with transaction.atomic():
                # Double vérification dans la transaction
                if AutomaticTransaction.objects.filter(source_id=source_id, transaction_type='recurring_income').exists():
                    return False
                
                # Créer la transaction automatique
                automatic_transaction = AutomaticTransaction.objects.create(
                    compte_reference=self.compte_reference,
                    montant=abs(self.montant),  # Positif pour les revenus
                    description=f"Revenu automatique - {self.type_revenu} - {self.description}",
                    date_transaction=today,
                    transaction_type='recurring_income',
                    source_id=source_id,
                    source_reference=str(self.id),
                    created_by=self.created_by
                )
                
                # Mettre à jour le solde du compte
                self.compte_reference.solde += automatic_transaction.montant
                self.compte_reference.save()
            
            # Mettre à jour la date de versement pour la prochaine occurrence
            next_income_date = self.get_next_occurrence(today)
            if next_income_date:
                # Utiliser update pour éviter de déclencher les signaux
                RecurringIncome.objects.filter(id=self.id).update(date_premier_versement=next_income_date)
                self.date_premier_versement = next_income_date
            
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

class AutomatedTask(BaseModel):
    """Modèle pour tracer les tâches automatiques exécutées"""
    TASK_TYPES = [
        ('PAYMENT_PROCESSING', 'Traitement des prélèvements'),
        ('INCOME_PROCESSING', 'Traitement des revenus'),
        ('BOTH_PROCESSING', 'Traitement complet'),
        ('MANUAL_EXECUTION', 'Exécution manuelle'),
        ('AUTO_TRIGGER', 'Déclenchement automatique'),
    ]
    
    STATUS_CHOICES = [
        ('SUCCESS', 'Succès'),
        ('ERROR', 'Erreur'),
        ('PARTIAL', 'Partiel'),
    ]
    
    task_type = models.CharField(max_length=50, choices=TASK_TYPES, verbose_name="Type de tâche")
    execution_date = models.DateTimeField(auto_now_add=True, verbose_name="Date d'exécution")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, verbose_name="Statut")
    processed_count = models.IntegerField(default=0, verbose_name="Nombre d'opérations traitées")
    error_message = models.TextField(blank=True, null=True, verbose_name="Message d'erreur")
    execution_duration = models.DecimalField(
        max_digits=10, 
        decimal_places=3, 
        null=True, 
        blank=True, 
        verbose_name="Durée d'exécution (secondes)"
    )
    details = models.JSONField(default=dict, blank=True, verbose_name="Détails de l'exécution")
    
    # Permettre created_by à être null pour les tâches automatiques
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='automated_tasks_created',
        null=True,
        blank=True,
        verbose_name="Créé par"
    )
    
    class Meta:
        verbose_name = "Tâche automatique"
        verbose_name_plural = "Tâches automatiques"
        ordering = ['-execution_date']
    
    def __str__(self):
        return f"{self.get_task_type_display()} - {self.execution_date.strftime('%d/%m/%Y %H:%M')} - {self.get_status_display()}"
    
    @classmethod
    def log_task(cls, task_type, status, processed_count=0, error_message=None, execution_duration=None, details=None, user=None):
        """Méthode utilitaire pour enregistrer une tâche automatique"""
        # Si aucun utilisateur n'est fourni, essayer de récupérer un utilisateur système
        if user is None:
            try:
                # Essayer de récupérer le premier utilisateur superuser ou le premier utilisateur
                user = User.objects.filter(is_superuser=True).first() or User.objects.first()
            except:
                user = None
        
        return cls.objects.create(
            task_type=task_type,
            status=status,
            processed_count=processed_count,
            error_message=error_message,
            execution_duration=execution_duration,
            details=details or {},
            created_by=user
        )

# Signaux pour le traitement automatique des prélèvements
@receiver(post_save, sender=DirectDebit)
def trigger_payment_processing(sender, instance, created, **kwargs):
    """
    Signal qui déclenche le traitement automatique des prélèvements
    lors de la création ou modification d'un DirectDebit
    """
    # Éviter le traitement automatique si c'est une mise à jour via update()
    # qui ne déclenche pas les signaux
    if not created and not hasattr(instance, '_state'):
        return
    
    start_time = time.time()
    
    try:
        if created:
            # Pour un nouveau prélèvement, vérifier s'il doit être traité immédiatement
            if instance.date_prelevement <= date.today() and instance.actif:
                processed = instance.process_due_payments()
                execution_duration = time.time() - start_time
                
                # Enregistrer la tâche automatique seulement si traitement effectué
                if processed:
                    AutomatedTask.log_task(
                        task_type='PAYMENT_PROCESSING',
                        status='SUCCESS',
                        processed_count=1,
                        execution_duration=execution_duration,
                        details={
                            'trigger': 'creation_prelevement',
                            'prelevement_id': instance.id,
                            'description': instance.description,
                            'date_prelevement': instance.date_prelevement.isoformat(),
                            'montant': str(instance.montant)
                        },
                        user=instance.created_by
                    )
        # Note: Les modifications sont maintenant gérées via update() qui ne déclenche pas les signaux
    
    except Exception as e:
        execution_duration = time.time() - start_time
        # Enregistrer l'erreur
        AutomatedTask.log_task(
            task_type='PAYMENT_PROCESSING',
            status='ERROR',
            processed_count=0,
            error_message=str(e),
            execution_duration=execution_duration,
            details={
                'trigger': 'creation_prelevement',
                'prelevement_id': instance.id,
                'description': instance.description
            },
            user=instance.created_by
        )

# Signaux pour le traitement automatique des revenus récurrents
@receiver(post_save, sender=RecurringIncome)
def trigger_income_processing(sender, instance, created, **kwargs):
    """
    Signal qui déclenche le traitement automatique des revenus récurrents
    lors de la création ou modification d'un RecurringIncome
    """
    # Éviter le traitement automatique si c'est une mise à jour via update()
    # qui ne déclenche pas les signaux
    if not created and not hasattr(instance, '_state'):
        return
    
    start_time = time.time()
    
    try:
        if created:
            # Pour un nouveau revenu, vérifier s'il doit être traité immédiatement
            if instance.date_premier_versement <= date.today() and instance.actif:
                processed = instance.process_due_income()
                execution_duration = time.time() - start_time
                
                # Enregistrer la tâche automatique seulement si traitement effectué
                if processed:
                    AutomatedTask.log_task(
                        task_type='INCOME_PROCESSING',
                        status='SUCCESS',
                        processed_count=1,
                        execution_duration=execution_duration,
                        details={
                            'trigger': 'creation_revenu',
                            'revenu_id': instance.id,
                            'type_revenu': instance.type_revenu,
                            'description': instance.description,
                            'date_premier_versement': instance.date_premier_versement.isoformat(),
                            'montant': str(instance.montant)
                        },
                        user=instance.created_by
                    )
        # Note: Les modifications sont maintenant gérées via update() qui ne déclenche pas les signaux
    
    except Exception as e:
        execution_duration = time.time() - start_time
        # Enregistrer l'erreur
        AutomatedTask.log_task(
            task_type='INCOME_PROCESSING',
            status='ERROR',
            processed_count=0,
            error_message=str(e),
            execution_duration=execution_duration,
            details={
                'trigger': 'creation_revenu',
                'revenu_id': instance.id,
                'type_revenu': instance.type_revenu,
                'description': instance.description
            },
            user=instance.created_by
        )
    
