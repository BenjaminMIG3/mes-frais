# Guide d'intégration API – Front-End (React Native)

Ce document a pour objectif de lister de manière exhaustive :

1. Les fonctionnalités d'interface à prévoir côté application mobile.
2. L'ensemble des endpoints REST exposés par l'API backend.

Aucun exemple de code n'est fourni volontairement ; le choix des bibliothèques, de l'architecture ou du style de programmation reste entièrement à la discrétion de l'équipe front-end.

---

## 1. Fonctionnalités à implémenter

### 1.1 Authentification & Gestion de session
• Formulaire de connexion (récupération d'un **access_token** & **refresh_token**).  
• Formulaire d'inscription.  
• Rafraîchissement silencieux du token d'accès.  
• Déconnexion utilisateur.  
• Écran « Profil » (données de l'utilisateur connecté).

### 1.2 Comptes bancaires
• Liste paginée des comptes de l'utilisateur.  
• Détail d'un compte avec : solde, historique d'opérations, statistiques.  
• Création, édition et suppression d'un compte.  
• Ajustement manuel du solde.  
• Vue « Résumé » (agrégation multi-comptes).

### 1.3 Opérations financières
• Liste filtrable & triable des opérations.  
• Détail / édition / suppression d'une opération.  
• Création d'opérations simples ou en lot.  
• Recherche avancée & statistiques globales.  
• Regroupement par compte.

### 1.4 Prélèvements automatiques
• Liste des prélèvements (actifs, expirés, à venir).  
• Création, édition, suppression, prolongation d'échéance.  
• Mise à jour groupée du statut.  
• Statistiques globales & vue par compte.  
• Tableau de bord synthétique.

### 1.5 Revenus récurrents
• Liste des revenus récurrents (actifs, à venir).  
• Création, édition, suppression, activation/désactivation.  
• Création en lot.  
• Statistiques globales, vue par compte et projections futures.

### 1.6 Projections budgétaires
• Création / gestion des projections sauvegardées.  
• Calcul en temps réel sans persistance.  
• Résumé budgétaire par compte ou global.  
• Tableau de bord consolidé (solde total, alertes, prochaines échéances).  
• Projection rapide (6 mois) & comparaison de scénarios.

### 1.7 Tâches automatiques - **NOUVEAU**
• **Historique des traitements** : Consultation de l'historique des tâches automatiques exécutées.
• **Statistiques de performance** : Taux de succès, durée moyenne d'exécution, nombre d'opérations traitées.
• **Monitoring en temps réel** : Alertes pour les tâches en erreur, activité récente (24h/7 jours).
• **Tableau de bord opérationnel** : Vue d'ensemble des traitements automatiques (prélèvements, revenus).
• **Gestion des erreurs** : Consultation des messages d'erreur et détails d'exécution.

### 1.8 Interface utilisateur et expérience
• **Gestion des thèmes** : Basculement entre mode sombre et mode clair avec persistance des préférences utilisateur.  
• **Support multilingue** : Interface entièrement traduite via i18n (français par défaut, anglais recommandé).  
• **Responsive design** : Adaptation optimale sur mobile, tablette et desktop.  
• **Accessibilité** : Conformité aux standards WCAG pour l'accessibilité.  
• **Animations fluides** : Transitions et micro-interactions pour une expérience moderne.  
• **Mode hors ligne** : Fonctionnalités de base disponibles sans connexion (cache local).  
• **Notifications push** : Alertes pour échéances de prélèvements et seuils de solde.

---

## 2. Base URL de l'API
```
/api/v1/
```
Tous les endpoints listés ci-dessous sont relatifs à cette racine.

---

## 3. Détails des endpoints

### 3.1 Authentification
Méthode | Chemin
--- | ---
POST | **auth/login/**
POST | **auth/register/**
POST | **auth/refresh_token/**
POST | **auth/logout/**
GET  | **auth/profile/**

### 3.2 Comptes (`accounts`)
Opération | Méthode | Chemin
--- | --- | ---
Lister | GET | **accounts/**
Créer | POST | **accounts/**
Détail | GET | **accounts/{id}/**
Mettre à jour | PUT/PATCH | **accounts/{id}/**
Supprimer | DELETE | **accounts/{id}/**
Résumé global | GET | **accounts/summary/**
Vue d'ensemble complète | GET | **accounts/global_overview/**
Opérations associées | GET | **accounts/{id}/operations/**
Statistiques | GET | **accounts/{id}/statistics/**
Ajuster le solde | POST | **accounts/{id}/adjust_balance/**

### 3.3 Opérations (`operations`)
Opération | Méthode | Chemin
--- | --- | ---
Lister | GET | **operations/**
Créer | POST | **operations/**
Détail | GET | **operations/{id}/**
Mettre à jour | PUT/PATCH | **operations/{id}/**
Supprimer | DELETE | **operations/{id}/**
Statistiques globales | GET | **operations/statistics/**
Recherche avancée | GET | **operations/search/**
Regroupement par compte | GET | **operations/by_account/**
Création en lot | POST | **operations/bulk_create/**

#### 3.3.1 Structure détaillée des réponses - Opérations

##### **GET /api/v1/operations/** - Liste des opérations

**Format de réponse standard (OperationListSerializer) :**
```json
[
  {
    "id": 1,
    "compte_reference_username": "john_doe",
    "montant": "250.00",
    "description": "Salaire mensuel",
    "created_at": "2024-01-15T10:30:00.123Z"
  },
  {
    "id": 2,
    "compte_reference_username": "jane_smith",
    "montant": "-45.50",
    "description": "Achat supermarché",
    "created_at": "2024-01-14T16:22:15.456Z"
  }
]
```

**Détails des champs :**

| Champ | Type | Description |
|-------|------|-------------|
| `id` | Integer | Identifiant unique de l'opération |
| `compte_reference_username` | String | Nom d'utilisateur du propriétaire du compte |
| `montant` | String (Decimal) | Montant de l'opération (positif = crédit, négatif = débit) |
| `description` | String | Description de l'opération (max 255 caractères) |
| `created_at` | String (ISO DateTime) | Date et heure de création de l'opération |

**Paramètres de requête disponibles :**
```json
{
  "compte_reference": "integer (optionnel) - Filtrer par ID de compte",
  "created_by": "integer (optionnel) - Filtrer par ID d'utilisateur créateur",
  "search": "string (optionnel) - Recherche dans la description",
  "ordering": "string (optionnel) - Tri (montant, created_at, updated_at, -created_at)",
  "page": "integer (optionnel) - Numéro de page pour la pagination",
  "page_size": "integer (optionnel) - Nombre d'éléments par page"
}
```

##### **GET /api/v1/operations/{id}/** - Détail d'une opération

**Format de réponse (OperationSerializer complet) :**
```json
{
  "id": 1,
  "compte_reference": 3,
  "compte_reference_username": "john_doe",
  "montant": "250.00",
  "description": "Salaire mensuel",
  "created_by": 1,
  "created_by_username": "admin",
  "created_at": "2024-01-15T10:30:00.123Z",
  "updated_at": "2024-01-15T10:30:00.123Z"
}
```

##### **GET /api/v1/operations/statistics/** - Statistiques globales

```json
{
  "statistics": {
    "total_operations": 150,
    "total_montant": 2500.75,
    "operations_30_jours": 45,
    "montant_30_jours": 1200.50,
    "operations_7_jours": 12,
    "montant_7_jours": 350.25,
    "operations_positives": 80,
    "montant_positif": 3200.00,
    "operations_negatives": 70,
    "montant_negatif": -700.25
  }
}
```

##### **GET /api/v1/operations/by_account/** - Opérations groupées par compte

```json
[
  {
    "account_id": 1,
    "account_username": "john_doe",
    "operations_count": 25,
    "total_montant": 1500.75,
    "operations": [
      {
        "id": 1,
        "montant": 250.00,
        "description": "Salaire",
        "created_at": "2024-01-15T10:30:00.123Z"
      },
      {
        "id": 2,
        "montant": -50.25,
        "description": "Achat",
        "created_at": "2024-01-14T15:20:00.456Z"
      }
    ]
  }
]
```

##### **GET /api/v1/operations/search/** - Recherche avancée

**Paramètres de recherche :**
```json
{
  "q": "string (optionnel) - Terme de recherche",
  "min_montant": "decimal (optionnel) - Montant minimum",
  "max_montant": "decimal (optionnel) - Montant maximum",
  "date_debut": "date (optionnel) - YYYY-MM-DD",
  "date_fin": "date (optionnel) - YYYY-MM-DD"
}
```

**Format de réponse :**
```json
{
  "query": "salaire",
  "filters": {
    "min_montant": "100.00",
    "max_montant": "500.00",
    "date_debut": "2024-01-01",
    "date_fin": "2024-01-31"
  },
  "results_count": 15,
  "operations": [
    {
      "id": 1,
      "compte_reference_username": "john_doe",
      "montant": "250.00",
      "description": "Salaire mensuel",
      "created_at": "2024-01-15T10:30:00.123Z"
    }
  ]
}
```

##### **POST /api/v1/operations/bulk_create/** - Création en lot

**Corps de la requête :**
```json
{
  "operations": [
    {
      "compte_reference": 1,
      "montant": "250.00",
      "description": "Salaire"
    },
    {
      "compte_reference": 1,
      "montant": "-45.50",
      "description": "Achat supermarché"
    }
  ]
}
```

**Format de réponse :**
```json
{
  "created_count": 2,
  "error_count": 0,
  "created_operations": [
    {
      "id": 10,
      "compte_reference_username": "john_doe",
      "montant": "250.00",
      "description": "Salaire",
      "created_at": "2024-01-15T10:30:00.123Z"
    },
    {
      "id": 11,
      "compte_reference_username": "john_doe",
      "montant": "-45.50",
      "description": "Achat supermarché",
      "created_at": "2024-01-15T10:30:05.678Z"
    }
  ],
  "errors": []
}
```

**En cas d'erreurs partielles :**
```json
{
  "created_count": 1,
  "error_count": 1,
  "created_operations": [
    {
      "id": 10,
      "compte_reference_username": "john_doe",
      "montant": "250.00",
      "description": "Salaire",
      "created_at": "2024-01-15T10:30:00.123Z"
    }
  ],
  "errors": [
    {
      "index": 1,
      "data": {
        "compte_reference": 999,
        "montant": "0.00",
        "description": ""
      },
      "errors": {
        "compte_reference": ["Le compte de référence spécifié n'existe pas."],
        "montant": ["Le montant ne peut pas être zéro."],
        "description": ["La description ne peut pas être vide."]
      }
    }
  ]
}
```

#### 3.3.2 Règles de validation - Opérations

**Règles métier importantes :**

1. **Montant** : Ne peut pas être égal à zéro (validation stricte)
2. **Description** : Ne peut pas être vide, maximum 255 caractères
3. **Compte de référence** : Doit exister et appartenir à l'utilisateur connecté
4. **Ajustement automatique du solde** : Le solde du compte est automatiquement mis à jour lors des opérations CRUD
5. **Filtrage par utilisateur** : Les utilisateurs ne voient que leurs propres opérations (sauf staff)

**Codes d'erreur courants :**
- `400` : Données de validation invalides
- `401` : Token d'authentification manquant ou invalide
- `403` : Accès refusé (tentative d'accès aux données d'un autre utilisateur)
- `404` : Opération ou compte non trouvé
- `500` : Erreur serveur interne

### 3.4 Prélèvements automatiques (`direct-debits`)
Opération | Méthode | Chemin
--- | --- | ---
Lister | GET | **direct-debits/**
Créer | POST | **direct-debits/**
Détail | GET | **direct-debits/{id}/**
Mettre à jour | PUT/PATCH | **direct-debits/{id}/**
Supprimer | DELETE | **direct-debits/{id}/**
Prélèvements actifs | GET | **direct-debits/active/**
Prélèvements expirés | GET | **direct-debits/expired/**
Prélèvements à venir | GET | **direct-debits/upcoming/**
Prolonger échéance | POST | **direct-debits/{id}/extend/**
Mise à jour groupée | POST | **direct-debits/bulk_status/**
Statistiques | GET | **direct-debits/statistics/**
Tableau de bord | GET | **direct-debits/dashboard/**

### 3.5 Revenus récurrents (`recurring-incomes`)
Opération | Méthode | Chemin
--- | --- | ---
Lister | GET | **recurring-incomes/**
Créer | POST | **recurring-incomes/**
Détail | GET | **recurring-incomes/{id}/**
Mettre à jour | PUT/PATCH | **recurring-incomes/{id}/**
Supprimer | DELETE | **recurring-incomes/{id}/**
Revenus actifs | GET | **recurring-incomes/active/**
Revenus à venir | GET | **recurring-incomes/upcoming/**
Création en lot | POST | **recurring-incomes/bulk_create/**
Activer/Désactiver | POST | **recurring-incomes/{id}/toggle/**
Statistiques | GET | **recurring-incomes/statistics/**
Projections futures | GET | **recurring-incomes/projections/**

### 3.6 Projections budgétaires (`budget-projections`)
Opération | Méthode | Chemin
--- | --- | ---
Lister | GET | **budget-projections/**
Créer | POST | **budget-projections/**
Détail | GET | **budget-projections/{id}/**
Mettre à jour | PUT/PATCH | **budget-projections/{id}/**
Supprimer | DELETE | **budget-projections/{id}/**
Calcul temps réel | POST | **budget-projections/calculate/**
Tableau de bord | GET | **budget-projections/dashboard/**
Comparaison scénarios | GET | **budget-projections/compare/**

### 3.7 Tâches automatiques (`automated-tasks`) - **NOUVEAU**
Opération | Méthode | Chemin
--- | --- | ---
Lister (lecture seule) | GET | **automated-tasks/**
Statistiques | GET | **automated-tasks/statistics/**
Tâches récentes (24h) | GET | **automated-tasks/recent/**
Tâches en erreur | GET | **automated-tasks/errors/**
Résumé | GET | **automated-tasks/summary/**

#### 3.7.1 Structure détaillée des réponses - Tâches automatiques

##### **GET /api/v1/automated-tasks/** - Liste des tâches automatiques

**Format de réponse standard (AutomatedTaskListSerializer) :**
```json
[
  {
    "id": 1,
    "task_type": "PAYMENT_PROCESSING",
    "task_type_display": "Traitement des prélèvements",
    "status": "SUCCESS",
    "status_display": "Succès",
    "processed_count": 3,
    "execution_date": "2024-01-15T10:30:00Z",
    "execution_date_formatted": "15/01/2024 10:30:00",
    "execution_duration": "0.125",
    "execution_duration_formatted": "0.125s",
    "created_by_username": "john_doe",
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

**Détails des champs :**

| Champ | Type | Description |
|-------|------|-------------|
| `id` | Integer | Identifiant unique de la tâche |
| `task_type` | String | Type de tâche (PAYMENT_PROCESSING, INCOME_PROCESSING, etc.) |
| `task_type_display` | String | Libellé lisible du type de tâche |
| `status` | String | Statut (SUCCESS, ERROR, PARTIAL) |
| `status_display` | String | Libellé lisible du statut |
| `processed_count` | Integer | Nombre d'opérations traitées |
| `execution_date` | String (ISO DateTime) | Date et heure d'exécution |
| `execution_date_formatted` | String | Date formatée pour l'affichage |
| `execution_duration` | String (Decimal) | Durée d'exécution en secondes |
| `execution_duration_formatted` | String | Durée formatée pour l'affichage |
| `created_by_username` | String | Nom d'utilisateur déclencheur |
| `created_at` | String (ISO DateTime) | Date et heure de création |

**Paramètres de requête disponibles :**
```json
{
  "task_type": "string (optionnel) - Filtrer par type de tâche",
  "status": "string (optionnel) - Filtrer par statut",
  "created_by": "integer (optionnel) - Filtrer par utilisateur déclencheur",
  "search": "string (optionnel) - Recherche dans les messages d'erreur",
  "ordering": "string (optionnel) - Tri (execution_date, processed_count, execution_duration)"
}
```

##### **GET /api/v1/automated-tasks/statistics/** - Statistiques des tâches

```json
{
  "task_types": {
    "PAYMENT_PROCESSING": {
      "total": 25,
      "success": 23,
      "error": 2,
      "success_rate": 92.0
    },
    "INCOME_PROCESSING": {
      "total": 15,
      "success": 15,
      "error": 0,
      "success_rate": 100.0
    }
  },
  "status_stats": {
    "SUCCESS": 38,
    "ERROR": 2,
    "PARTIAL": 0
  },
  "performance": {
    "average_duration_seconds": 0.125,
    "total_tasks": 40,
    "total_processed_operations": 150
  },
  "recent_activity": {
    "last_7_days_tasks": 8,
    "last_7_days_processed": 25
  }
}
```

##### **GET /api/v1/automated-tasks/recent/** - Tâches récentes (24h)

```json
{
  "count": 3,
  "tasks": [
    {
      "id": 1,
      "task_type_display": "Traitement des prélèvements",
      "status_display": "Succès",
      "processed_count": 2,
      "execution_date_formatted": "15/01/2024 10:30:00",
      "execution_duration": "0.125"
    }
  ]
}
```

##### **GET /api/v1/automated-tasks/errors/** - Tâches en erreur

```json
{
  "count": 2,
  "tasks": [
    {
      "id": 5,
      "task_type_display": "Traitement des prélèvements",
      "status_display": "Erreur",
      "error_message": "Compte insuffisamment approvisionné",
      "execution_date_formatted": "15/01/2024 09:15:00"
    }
  ]
}
```

##### **GET /api/v1/automated-tasks/summary/** - Résumé des tâches

```json
{
  "today": {
    "tasks_count": 5,
    "processed_operations": 12
  },
  "this_week": {
    "tasks_count": 25,
    "processed_operations": 45
  },
  "this_month": {
    "tasks_count": 95,
    "processed_operations": 180
  },
  "total": {
    "tasks_count": 150,
    "processed_operations": 280
  }
}
```

---

## 4. Système de traitement automatique

### 4.1 Signaux automatiques

L'API intègre un système de signaux Django qui déclenche automatiquement le traitement des prélèvements et revenus :

#### **Traitement des prélèvements**
- **Déclenchement** : Création ou modification d'un prélèvement automatique
- **Condition** : Date de prélèvement ≤ date actuelle ET prélèvement actif
- **Action** : Création automatique d'une opération de débit
- **Mise à jour** : Solde du compte et prochaine date de prélèvement
- **Traçabilité** : Enregistrement d'une tâche automatique

#### **Traitement des revenus**
- **Déclenchement** : Création ou modification d'un revenu récurrent
- **Condition** : Date de premier versement ≤ date actuelle ET revenu actif
- **Action** : Création automatique d'une opération de crédit
- **Mise à jour** : Solde du compte et prochaine date de versement
- **Traçabilité** : Enregistrement d'une tâche automatique

### 4.2 Types de tâches automatiques

| Type | Description | Déclenchement |
|------|-------------|---------------|
| `PAYMENT_PROCESSING` | Traitement des prélèvements | Création/modification de DirectDebit |
| `INCOME_PROCESSING` | Traitement des revenus | Création/modification de RecurringIncome |
| `BOTH_PROCESSING` | Traitement complet | Script de gestion manuel |
| `MANUAL_EXECUTION` | Exécution manuelle | Action utilisateur |
| `AUTO_TRIGGER` | Déclenchement automatique | Système automatique |

### 4.3 Statuts des tâches

| Statut | Description |
|--------|-------------|
| `SUCCESS` | Tâche exécutée avec succès |
| `ERROR` | Erreur lors de l'exécution |
| `PARTIAL` | Exécution partielle (certaines opérations échouées) |

---

## 5. Gestion des erreurs

### 5.1 Codes de réponse HTTP

| Code | Description | Utilisation |
|------|-------------|-------------|
| 200 | Succès | GET, PUT, PATCH |
| 201 | Créé | POST |
| 204 | Succès sans contenu | DELETE |
| 400 | Erreur de validation | Données invalides |
| 401 | Non authentifié | Token manquant/invalide |
| 403 | Accès interdit | Permissions insuffisantes |
| 404 | Ressource non trouvée | ID inexistant |
| 500 | Erreur serveur | Erreur interne |

### 5.2 Format des erreurs

```json
{
  "error": "Message d'erreur principal",
  "details": {
    "field_name": ["Message d'erreur spécifique"]
  },
  "code": "ERROR_CODE_OPTIONNEL"
}
```

---

## 6. Authentification et sécurité

### 6.1 Headers requis

```http
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
```

### 6.2 Gestion des tokens

- **Access Token** : Valide 1 heure
- **Refresh Token** : Valide 7 jours
- **Renouvellement automatique** : Via `/auth/refresh_token/`

### 6.3 Isolation des données

- Chaque utilisateur accède uniquement à ses propres données
- Filtrage automatique par utilisateur connecté
- Permissions staff pour accès global (administration)

---

## 7. Optimisations et bonnes pratiques

### 7.1 Pagination

Toutes les listes sont paginées par défaut :
```http
GET /api/v1/operations/?page=1&page_size=20
```

### 7.2 Filtrage et recherche

Utilisation des paramètres de requête pour optimiser les performances :
```http
GET /api/v1/operations/?compte_reference=1&search=salaire&ordering=-created_at
```

### 7.3 Cache et performance

- **Cache local** : Mise en cache des données fréquemment consultées
- **Requêtes optimisées** : Utilisation des endpoints de statistiques plutôt que de calculs côté client
- **Lazy loading** : Chargement à la demande des données détaillées

### 7.4 Gestion hors ligne

- **Cache local** : Stockage des données essentielles
- **Synchronisation** : Mise à jour lors du retour en ligne
- **Validation locale** : Vérification des données avant envoi

---

## 8. Tests et développement

### 8.1 Environnement de test

- **Base URL de test** : `/api/v1/`
- **Données de test** : Génération automatique via scripts
- **Tests automatisés** : Suite complète de tests unitaires et d'intégration

### 8.2 Outils de développement

- **Documentation interactive** : Endpoints documentés avec exemples
- **Logs détaillés** : Traçabilité complète des opérations
- **Monitoring** : Statistiques de performance et alertes

---

## 9. Déploiement et production

### 9.1 Configuration recommandée

- **Base de données** : PostgreSQL pour la précision financière
- **Cache** : Redis pour les sessions et données temporaires
- **Monitoring** : Logs structurés et métriques de performance

### 9.2 Sécurité en production

- **HTTPS obligatoire** : Toutes les communications chiffrées
- **Rate limiting** : Protection contre les abus
- **Validation stricte** : Vérification de toutes les données d'entrée
- **Audit trail** : Traçabilité complète des modifications

---

## 10. Support et maintenance

### 10.1 Documentation

- **API Documentation** : Documentation complète et mise à jour
- **Changelog** : Historique des modifications
- **Exemples d'utilisation** : Cas d'usage courants

### 10.2 Monitoring

- **Statistiques de performance** : Temps de réponse, taux d'erreur
- **Alertes automatiques** : Notifications en cas de problème
- **Tableau de bord opérationnel** : Vue d'ensemble du système

Cette documentation est régulièrement mise à jour pour refléter les dernières évolutions de l'API. Pour toute question ou suggestion d'amélioration, n'hésitez pas à contacter l'équipe de développement.