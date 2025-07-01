from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.contrib.admin import AdminSite

# Ajoute les models de models.py
from my_frais.models import Account, Operation, DirectDebit, RecurringIncome, BudgetProjection, AutomatedTask, AutomaticTransaction


# ozdjuzndzndzun

class BaseModelAdmin(admin.ModelAdmin):
    """Classe de base pour l'administration des modèles avec champs communs"""
    readonly_fields = ('created_at', 'updated_at')
    
    def get_readonly_fields(self, request, obj=None):
        """Rend created_by en lecture seule lors de la modification"""
        if obj:  # Modification d'un objet existant
            return self.readonly_fields + ('created_by',)
        return self.readonly_fields
    
    def save_model(self, request, obj, form, change):
        """Assigne automatiquement l'utilisateur créateur"""
        if not change:  # Nouvel objet
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Account)
class AccountAdmin(BaseModelAdmin):
    """Administration des comptes bancaires"""
    list_display = ('nom', 'user', 'solde_formatted', 'nombre_operations', 'created_at', 'created_by')
    list_filter = ('created_at', 'updated_at', 'user')
    search_fields = ('nom', 'user__username', 'user__email')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Informations du compte', {
            'fields': ('user', 'nom', 'solde')
        }),
        ('Métadonnées', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def solde_formatted(self, obj):
        """Formatage du solde avec couleur selon le montant"""
        color = 'green' if obj.solde >= 0 else 'red'
        return format_html(
            '<span style="color: {};">{} €</span>',
            color,
            f"{obj.solde:.2f}"
        )
    solde_formatted.short_description = 'Solde'
    solde_formatted.admin_order_field = 'solde'
    
    def nombre_operations(self, obj):
        """Compte le nombre d'opérations liées au compte"""
        count = obj.operations.count()
        url = reverse('admin:my_frais_operation_changelist') + f'?compte_reference__id__exact={obj.id}'
        return format_html('<a href="{}">{} opération(s)</a>', url, count)
    nombre_operations.short_description = 'Opérations'


@admin.register(Operation)
class OperationAdmin(BaseModelAdmin):
    """Administration des opérations"""
    list_display = ('description', 'compte_reference', 'montant_formatted', 'date_operation', 'created_by')
    list_filter = ('date_operation', 'created_at', 'compte_reference', 'compte_reference__user')
    search_fields = ('description', 'compte_reference__nom', 'compte_reference__user__username')
    date_hierarchy = 'date_operation'
    ordering = ('-date_operation', '-created_at')
    
    fieldsets = (
        ('Informations de l\'opération', {
            'fields': ('compte_reference', 'description', 'montant', 'date_operation')
        }),
        ('Métadonnées', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def montant_formatted(self, obj):
        """Formatage du montant avec couleur selon le signe"""
        color = 'green' if obj.montant >= 0 else 'red'
        sign = '+' if obj.montant >= 0 else ''
        return format_html(
            '<span style="color: {};">{}{} €</span>',
            color,
            sign,
            f"{obj.montant:.2f}"
        )
    montant_formatted.short_description = 'Montant'
    montant_formatted.admin_order_field = 'montant'
    
    def get_queryset(self, request):
        """Optimise les requêtes avec select_related"""
        return super().get_queryset(request).select_related('compte_reference', 'compte_reference__user', 'created_by')


@admin.register(DirectDebit)
class DirectDebitAdmin(OperationAdmin):
    """Administration des prélèvements automatiques"""
    list_display = ('description', 'compte_reference', 'montant_formatted', 'date_prelevement', 
                    'frequence', 'actif_status', 'echeance_info', 'created_by')
    list_filter = ('frequence', 'actif', 'date_prelevement', 'echeance', 'created_at', 
                   'compte_reference', 'compte_reference__user')
    search_fields = ('description', 'compte_reference__nom', 'compte_reference__user__username')
    date_hierarchy = 'date_prelevement'
    ordering = ('-date_prelevement', '-created_at')
    
    # Ajout des champs en lecture seule spécifiques à DirectDebit
    readonly_fields = ('created_at', 'updated_at', 'date_operation')
    
    def get_readonly_fields(self, request, obj=None):
        """Gère les champs en lecture seule pour DirectDebit"""
        if obj:  # Modification d'un objet existant
            return self.readonly_fields + ('created_by',)
        return self.readonly_fields
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('compte_reference', 'description', 'montant')
        }),
        ('Configuration du prélèvement', {
            'fields': ('date_prelevement', 'frequence', 'actif', 'echeance'),
            'description': 'Paramètres spécifiques au prélèvement automatique'
        }),
        ('Métadonnées', {
            'fields': ('date_operation', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def actif_status(self, obj):
        """Statut actif avec icône"""
        if obj.actif:
            return format_html('<span style="color: green;">✓ Actif</span>')
        else:
            return format_html('<span style="color: red;">✗ Inactif</span>')
    actif_status.short_description = 'Statut'
    actif_status.admin_order_field = 'actif'
    
    def echeance_info(self, obj):
        """Informations sur l'échéance"""
        if obj.echeance:
            return format_html(
                '<span style="color: orange;">📅 {}</span>',
                obj.echeance.strftime('%d/%m/%Y')
            )
        return format_html('<span style="color: gray;">Aucune échéance</span>')
    echeance_info.short_description = 'Échéance'
    echeance_info.admin_order_field = 'echeance'
    
    actions = ['activer_prelevements', 'desactiver_prelevements']
    
    def activer_prelevements(self, request, queryset):
        """Action pour activer plusieurs prélèvements"""
        updated = queryset.update(actif=True)
        self.message_user(request, f'{updated} prélèvement(s) activé(s) avec succès.')
    activer_prelevements.short_description = "Activer les prélèvements sélectionnés"
    
    def desactiver_prelevements(self, request, queryset):
        """Action pour désactiver plusieurs prélèvements"""
        updated = queryset.update(actif=False)
        self.message_user(request, f'{updated} prélèvement(s) désactivé(s) avec succès.')
    desactiver_prelevements.short_description = "Désactiver les prélèvements sélectionnés"


@admin.register(RecurringIncome)
class RecurringIncomeAdmin(admin.ModelAdmin):
    """Administration des revenus récurrents"""
    list_display = ['description', 'type_revenu', 'montant', 'frequence', 'compte_reference', 'actif', 'date_premier_versement', 'date_fin']
    list_filter = ['type_revenu', 'frequence', 'actif', 'created_at']
    search_fields = ['description', 'type_revenu', 'compte_reference__nom', 'compte_reference__user__username']
    readonly_fields = ['created_by', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('description', 'type_revenu', 'montant', 'compte_reference')
        }),
        ('Récurrence', {
            'fields': ('frequence', 'date_premier_versement', 'date_fin', 'actif')
        }),
        ('Métadonnées', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Nouvel objet
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(BudgetProjection)
class BudgetProjectionAdmin(admin.ModelAdmin):
    """Administration des projections de budget"""
    list_display = ['compte_reference', 'date_projection', 'periode_projection', 'solde_initial', 'created_at']
    list_filter = ['periode_projection', 'date_projection', 'created_at']
    search_fields = ['compte_reference__nom', 'compte_reference__user__username']
    readonly_fields = ['created_by', 'created_at', 'updated_at', 'projections_data']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Projection', {
            'fields': ('compte_reference', 'date_projection', 'periode_projection', 'solde_initial')
        }),
        ('Données calculées', {
            'fields': ('projections_data',),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Nouvel objet
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(AutomatedTask)
class AutomatedTaskAdmin(admin.ModelAdmin):
    """Administration des tâches automatiques"""
    list_display = ('task_type_display', 'status_display', 'processed_count', 'execution_date', 'execution_duration_display', 'created_by')
    list_filter = ('task_type', 'status', 'execution_date', 'created_at')
    search_fields = ('task_type', 'error_message', 'created_by__username')
    readonly_fields = ('created_by', 'created_at', 'updated_at', 'execution_date', 'details_formatted')
    ordering = ('-execution_date',)
    
    fieldsets = (
        ('Informations de la tâche', {
            'fields': ('task_type', 'status', 'processed_count', 'execution_date', 'execution_duration')
        }),
        ('Détails d\'exécution', {
            'fields': ('error_message', 'details_formatted'),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def task_type_display(self, obj):
        """Affichage du type de tâche avec icône"""
        icons = {
            'PAYMENT_PROCESSING': '💳',
            'INCOME_PROCESSING': '💰',
            'BOTH_PROCESSING': '🔄',
            'MANUAL_EXECUTION': '👤',
            'AUTO_TRIGGER': '⚡',
        }
        icon = icons.get(obj.task_type, '⚙️')
        return format_html('{} {}', icon, obj.get_task_type_display())
    task_type_display.short_description = 'Type de tâche'
    task_type_display.admin_order_field = 'task_type'
    
    def status_display(self, obj):
        """Affichage du statut avec couleur"""
        colors = {
            'SUCCESS': 'green',
            'ERROR': 'red',
            'PARTIAL': 'orange',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {};">● {}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'Statut'
    status_display.admin_order_field = 'status'
    
    def execution_duration_display(self, obj):
        """Affichage de la durée d'exécution"""
        if obj.execution_duration:
            return f"{obj.execution_duration:.3f}s"
        return "N/A"
    execution_duration_display.short_description = 'Durée'
    execution_duration_display.admin_order_field = 'execution_duration'
    
    def details_formatted(self, obj):
        """Affichage formaté des détails JSON"""
        if not obj.details:
            return "Aucun détail"
        
        html = "<div style='font-family: monospace; background: #f5f5f5; padding: 10px; border-radius: 4px;'>"
        for key, value in obj.details.items():
            html += f"<strong>{key}:</strong> {value}<br>"
        html += "</div>"
        return format_html(html)
    details_formatted.short_description = 'Détails de l\'exécution'
    
    def get_queryset(self, request):
        """Optimise les requêtes avec select_related"""
        return super().get_queryset(request).select_related('created_by')
    
    actions = ['reprocess_failed_tasks']
    
    def reprocess_failed_tasks(self, request, queryset):
        """Action pour reprocesser les tâches en erreur"""
        failed_tasks = queryset.filter(status='ERROR')
        count = failed_tasks.count()
        self.message_user(request, f'{count} tâche(s) en erreur sélectionnée(s) pour reprocessing.')
    reprocess_failed_tasks.short_description = "Reprocesser les tâches en erreur sélectionnées"


# Configuration globale de l'admin
admin.site.site_header = "Mes Frais - Administration"
admin.site.site_title = "Mes Frais Admin"
admin.site.index_title = "Gestion des comptes et opérations"

# Personnalisation de l'admin site pour ajouter les liens MongoDB
original_get_app_list = admin.site.get_app_list

def get_app_list_with_mongodb(request):
    app_list = original_get_app_list(request)
    
    # Ajouter un lien vers les logs MongoDB
    if request.user.is_staff:
        mongodb_app = {
            'name': 'MongoDB Logs',
            'app_label': 'mongodb_logs',
            'app_url': reverse('mongodb_logs:dashboard'),
            'has_module_perms': True,
            'models': [
                {
                    'name': 'Tableau de bord',
                    'object_name': 'dashboard',
                    'admin_url': reverse('mongodb_logs:dashboard'),
                    'view_only': True,
                },
                {
                    'name': 'Logs d\'authentification',
                    'object_name': 'auth_events',
                    'admin_url': reverse('mongodb_logs:auth'),
                    'view_only': True,
                },
                {
                    'name': 'Logs CRUD',
                    'object_name': 'crud_events',
                    'admin_url': reverse('mongodb_logs:crud'),
                    'view_only': True,
                },
                {
                    'name': 'Logs d\'erreurs',
                    'object_name': 'errors',
                    'admin_url': reverse('mongodb_logs:errors'),
                    'view_only': True,
                },
                {
                    'name': 'Logs métier',
                    'object_name': 'business_events',
                    'admin_url': reverse('mongodb_logs:business'),
                    'view_only': True,
                },
            ]
        }
        app_list.append(mongodb_app)
    
    return app_list

# Remplacer la méthode get_app_list
admin.site.get_app_list = get_app_list_with_mongodb
