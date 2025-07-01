# Mes Frais - Application de Gestion Financière

## 🚀 Fonctionnalités Mises en Place

### 🔐 Authentification
- Système d'authentification JWT
- API d'inscription et connexion
- Gestion des tokens d'accès et de rafraîchissement
- Profil utilisateur

### 🏦 Gestion des Comptes
- Création et gestion de comptes bancaires
- Suivi automatique des soldes
- Statistiques par compte
- Vue d'ensemble multi-comptes

### 💰 Opérations Financières
- Création et gestion d'opérations
- Recherche et filtrage avancés
- Création en lot
- Statistiques globales
- Regroupement par compte

### 🔄 Prélèvements Automatiques
- Gestion des prélèvements récurrents
- Fréquences : mensuel, trimestriel, annuel
- Traitement automatique des échéances
- Gestion des dates de fin
- Statistiques des prélèvements

### 💵 Revenus Récurrents
- Gestion des revenus récurrents
- Fréquences : hebdomadaire, mensuel, trimestriel, annuel
- Traitement automatique des versements
- Types de revenus configurables
- Projections de revenus

### 📊 Projections Budgétaires
- Calcul de projections sur 6 mois
- Sauvegarde des projections
- Comparaison de scénarios
- Tableau de bord consolidé
- Alertes de seuils

### 🤖 Tâches Automatiques
- Traitement automatique des prélèvements
- Traitement automatique des revenus
- Historique des exécutions
- Monitoring des performances
- Gestion des erreurs

### 📈 Statistiques et Analyses
- Statistiques par compte
- Statistiques globales
- Analyses temporelles (7 jours, 30 jours)
- Tableaux de bord synthétiques

### 🔧 Outils de Développement
- Scripts de génération de données de test
- Scripts de génération de logs
- Gestion des prélèvements automatiques
- Tests automatisés avec pytest

### 🛠️ Architecture Technique
- API REST Django avec Django REST Framework
- Base de données MySQL
- Authentification JWT
- Sérialiseurs personnalisés
- ViewSets avec actions spécialisées
- Middleware de logging
- Services MongoDB pour les logs

### 📋 Modèles de Données
- Account (Comptes bancaires)
- Operation (Opérations financières)
- DirectDebit (Prélèvements automatiques)
- RecurringIncome (Revenus récurrents)
- BudgetProjection (Projections budgétaires)
- AutomatedTask (Tâches automatiques)
- AutomaticTransaction (Transactions automatiques)

### 🌐 API Endpoints
- 58 routes API au total
- CRUD complet pour tous les modèles
- Actions spécialisées par domaine
- Recherche et filtrage avancés
- Pagination et tri

### 📚 Documentation
- Documentation API complète
- Guide d'intégration front-end
- Exemples de requêtes et réponses
- Structure des modèles de données