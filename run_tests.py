#!/usr/bin/env python3
"""
Script de lancement des tests unitaires pour le projet mes-frais.
Fournit des options pour exécuter des tests spécifiques et générer des rapports.
"""

import os
import sys
import django
import subprocess
from datetime import datetime

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()


def print_banner():
    """Affiche la bannière du script de tests"""
    print("=" * 80)
    print("🧪 SCRIPT DE TESTS UNITAIRES - MES FRAIS")
    print("=" * 80)
    print(f"📅 Démarré le : {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}")
    print("=" * 80)


def print_section(title):
    """Affiche un titre de section"""
    print(f"\n📋 {title}")
    print("-" * (len(title) + 4))


def run_command(command, description):
    """Exécute une commande et affiche le résultat"""
    print(f"\n🔄 {description}...")
    print(f"💻 Commande : {command}")
    print("─" * 50)
    
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True,
            check=False
        )
        
        if result.stdout:
            print(result.stdout)
        
        if result.stderr and result.returncode != 0:
            print(f"❌ Erreur : {result.stderr}")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Erreur lors de l'exécution : {e}")
        return False


def run_auth_tests():
    """Exécute les tests de l'application auth_api"""
    print_section("TESTS DE L'APPLICATION AUTH_API")
    
    commands = [
        ("python manage.py test auth_api.tests.AuthSerializerTestCase --verbosity=2", 
         "Tests du serializer d'authentification"),
        ("python manage.py test auth_api.tests.JWTAuthenticationTestCase --verbosity=2", 
         "Tests de l'authentification JWT"),
        ("python manage.py test auth_api.tests.AuthViewSetTestCase --verbosity=2", 
         "Tests des vues d'authentification"),
        ("python manage.py test auth_api.tests.AuthIntegrationTestCase --verbosity=2", 
         "Tests d'intégration authentification")
    ]
    
    success_count = 0
    for command, description in commands:
        if run_command(command, description):
            success_count += 1
    
    print(f"\n✅ Tests auth_api : {success_count}/{len(commands)} réussis")
    return success_count == len(commands)


def run_my_frais_tests():
    """Exécute les tests de l'application my_frais"""
    print_section("TESTS DE L'APPLICATION MY_FRAIS")
    
    commands = [
        ("python manage.py test my_frais.tests.AccountModelTestCase --verbosity=2", 
         "Tests du modèle Account"),
        ("python manage.py test my_frais.tests.OperationModelTestCase --verbosity=2", 
         "Tests du modèle Operation"),
        ("python manage.py test my_frais.tests.DirectDebitModelTestCase --verbosity=2", 
         "Tests du modèle DirectDebit"),
        ("python manage.py test my_frais.tests.RecurringIncomeModelTestCase --verbosity=2", 
         "Tests du modèle RecurringIncome"),
        ("python manage.py test my_frais.tests.BudgetProjectionModelTestCase --verbosity=2", 
         "Tests du modèle BudgetProjection"),
        ("python manage.py test my_frais.tests.AccountSerializerTestCase --verbosity=2", 
         "Tests du serializer Account"),
        ("python manage.py test my_frais.tests.AccountViewSetTestCase --verbosity=2", 
         "Tests du ViewSet Account"),
        ("python manage.py test my_frais.tests.MyFraisIntegrationTestCase --verbosity=2", 
         "Tests d'intégration my_frais")
    ]
    
    success_count = 0
    for command, description in commands:
        if run_command(command, description):
            success_count += 1
    
    print(f"\n✅ Tests my_frais : {success_count}/{len(commands)} réussis")
    return success_count == len(commands)


def run_all_tests():
    """Exécute tous les tests"""
    print_section("EXÉCUTION DE TOUS LES TESTS")
    
    return run_command(
        "python manage.py test --verbosity=2 --parallel --keepdb", 
        "Tous les tests (en parallèle)"
    )


def run_coverage_tests():
    """Exécute les tests avec couverture de code"""
    print_section("TESTS AVEC COUVERTURE DE CODE")
    
    # Vérifier si coverage est installé
    try:
        import coverage
        print("✅ Module coverage détecté")
    except ImportError:
        print("⚠️  Module coverage non installé. Installation...")
        if not run_command("pip install coverage", "Installation de coverage"):
            print("❌ Impossible d'installer coverage")
            return False
    
    commands = [
        ("coverage run --source='.' manage.py test --verbosity=2", 
         "Exécution des tests avec coverage"),
        ("coverage report --omit='*/migrations/*,*/venv/*,*/env/*,manage.py,*/settings.py'", 
         "Rapport de couverture"),
        ("coverage html --omit='*/migrations/*,*/venv/*,*/env/*,manage.py,*/settings.py'", 
         "Génération du rapport HTML")
    ]
    
    success_count = 0
    for command, description in commands:
        if run_command(command, description):
            success_count += 1
    
    if success_count == len(commands):
        print("\n📊 Rapport de couverture HTML généré dans 'htmlcov/index.html'")
    
    return success_count == len(commands)


def check_code_quality():
    """Vérifie la qualité du code avec flake8"""
    print_section("VÉRIFICATION DE LA QUALITÉ DU CODE")
    
    try:
        import flake8
        print("✅ Module flake8 détecté")
    except ImportError:
        print("⚠️  Module flake8 non installé. Installation...")
        if not run_command("pip install flake8", "Installation de flake8"):
            print("❌ Impossible d'installer flake8")
            return False
    
    return run_command(
        "flake8 auth_api my_frais --max-line-length=120 --exclude=migrations,__pycache__", 
        "Vérification avec flake8"
    )


def generate_test_report():
    """Génère un rapport de test détaillé"""
    print_section("GÉNÉRATION DU RAPPORT DE TEST DÉTAILLÉ")
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f"test_report_{timestamp}.txt"
    
    command = f"python manage.py test --verbosity=2 > {report_file} 2>&1"
    
    if run_command(command, f"Génération du rapport dans {report_file}"):
        print(f"📄 Rapport détaillé sauvegardé : {report_file}")
        return True
    return False


def main():
    """Fonction principale"""
    print_banner()
    
    if len(sys.argv) > 1:
        option = sys.argv[1]
        
        if option == "auth":
            success = run_auth_tests()
        elif option == "my_frais":
            success = run_my_frais_tests()
        elif option == "all":
            success = run_all_tests()
        elif option == "coverage":
            success = run_coverage_tests()
        elif option == "quality":
            success = check_code_quality()
        elif option == "report":
            success = generate_test_report()
        else:
            print(f"❌ Option '{option}' non reconnue")
            print_usage()
            sys.exit(1)
    else:
        # Par défaut, exécuter tous les tests
        print("🚀 Exécution de tous les tests par défaut...")
        
        # Exécuter les tests par application
        auth_success = run_auth_tests()
        my_frais_success = run_my_frais_tests()
        
        # Résumé final
        print_section("RÉSUMÉ FINAL")
        print(f"✅ Tests auth_api : {'RÉUSSIS' if auth_success else 'ÉCHOUÉS'}")
        print(f"✅ Tests my_frais : {'RÉUSSIS' if my_frais_success else 'ÉCHOUÉS'}")
        
        success = auth_success and my_frais_success
    
    # Conclusion
    print("\n" + "=" * 80)
    if success:
        print("🎉 TOUS LES TESTS SONT RÉUSSIS !")
        print("✅ Votre code est prêt pour la production")
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        print("⚠️  Veuillez corriger les erreurs avant de continuer")
    print("=" * 80)
    
    # Code de sortie
    sys.exit(0 if success else 1)


def print_usage():
    """Affiche l'aide d'utilisation"""
    print("\n📖 UTILISATION :")
    print("  python run_tests.py [option]")
    print("\n🔧 OPTIONS DISPONIBLES :")
    print("  auth      - Exécuter uniquement les tests de auth_api")
    print("  my_frais  - Exécuter uniquement les tests de my_frais")
    print("  all       - Exécuter tous les tests (en parallèle)")
    print("  coverage  - Exécuter les tests avec couverture de code")
    print("  quality   - Vérifier la qualité du code avec flake8")
    print("  report    - Générer un rapport de test détaillé")
    print("  (aucune)  - Exécuter tous les tests par application")
    print("\n💡 EXEMPLES :")
    print("  python run_tests.py auth")
    print("  python run_tests.py coverage")
    print("  python run_tests.py")


if __name__ == "__main__":
    main() 