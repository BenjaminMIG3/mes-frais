# Generated by Django 5.2.3 on 2025-06-30 15:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('my_frais', '0005_alter_automatedtask_created_by'),
    ]

    operations = [
        migrations.AlterField(
            model_name='automatedtask',
            name='task_type',
            field=models.CharField(choices=[('PAYMENT_PROCESSING', 'Traitement des prélèvements'), ('INCOME_PROCESSING', 'Traitement des revenus'), ('BOTH_PROCESSING', 'Traitement complet'), ('MANUAL_EXECUTION', 'Exécution manuelle'), ('AUTO_TRIGGER', 'Déclenchement automatique')], max_length=50, verbose_name='Type de tâche'),
        ),
    ]
