# 📊 API Documentation - Mes Frais

Cette documentation présente une API REST complète pour la gestion de frais personnels et budgets familiaux. L'API permet de gérer des comptes bancaires, opérations financières, prélèvements automatiques, revenus récurrents, projections budgétaires et **tâches automatiques**.

## 🏗️ Architecture et Relations

### Modèle de Données Hiérarchique :
```
User (Utilisateur Django)
├── Account (Compte bancaire)
│   ├── Operation (Opération financière)
│   │   └── DirectDebit (Prélèvement - hérite d'Operation)
│   ├── RecurringIncome (Revenu récurrent)
│   └── BudgetProjection (Projection budgétaire)
└── AutomatedTask (Tâche automatique - traçabilité)
```

### Relations Clés :
- **User → Account** : Un utilisateur peut avoir plusieurs comptes
- **Account → Operation** : Un compte a plusieurs opérations (1-N)
- **Operation → DirectDebit** : Les prélèvements sont des opérations spécialisées (héritage)
- **Account → RecurringIncome** : Un compte peut avoir plusieurs revenus récurrents (1-N)
- **Account → BudgetProjection** : Un compte peut avoir plusieurs projections (1-N)
- **User → AutomatedTask** : Un utilisateur peut avoir plusieurs tâches automatiques (1-N)

## 🔐 Authentification & Sécurité

**Système d'authentification :** Token JWT requis pour toutes les routes
**Base URL :** `/api/`
**Isolation des données :** Chaque utilisateur accède uniquement à ses propres données
**Permissions Staff :** Les utilisateurs staff peuvent accéder à toutes les données

### Headers requis :
```http
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
```

## 🎯 Conventions Générales

### Formats de Données :
- **IDs** : Entiers positifs
- **Montants** : Strings avec décimales (`"1250.75"`) pour précision financière
- **Dates** : Format ISO `YYYY-MM-DD`
- **Timestamps** : Format ISO `YYYY-MM-DDTHH:MM:SSZ`
- **Booléens** : `true`/`false`

### Codes de Réponse HTTP :
- **200** : Succès (GET, PUT, PATCH)
- **201** : Créé (POST)
- **204** : Succès sans contenu (DELETE)
- **400** : Erreur de validation
- **401** : Non authentifié
- **403** : Accès interdit
- **404** : Ressource non trouvée

## 📋 Résumé des Endpoints (58 routes total)

| Modèle | Routes CRUD | Actions Spécialisées | Total |
|--------|-------------|---------------------|-------|
| **Account** | 5 | 5 | 10 |
| **Operation** | 5 | 3 | 8 |
| **DirectDebit** | 5 | 7 | 12 |
| **RecurringIncome** | 5 | 6 | 11 |
| **BudgetProjection** | 5 | 3 | 8 |
| **AutomatedTask** | 1 | 4 | 5 |

### Actions les Plus Importantes pour un LLM :
1. **`GET /accounts/`** - Point d'entrée principal
2. **`GET /accounts/{id}/statistics/`** - Résumé d'un compte
3. **`GET /budget-projections/dashboard/`** - Vue d'ensemble complète
4. **`POST /budget-projections/calculate/`** - Projections temps réel
5. **`GET /operations/search/`** - Recherche avancée d'opérations
6. **`GET /automated-tasks/statistics/`** - Statistiques des tâches automatiques

### Logique des Relations :
- **User** ← has many → **Account** ← has many → **Operation/DirectDebit/RecurringIncome/BudgetProjection**
- **DirectDebit** IS-A **Operation** (héritage)
- **User** ← has many → **AutomatedTask** (traçabilité)
- Toutes les modifications d'**Operation** mettent à jour **Account.solde** automatiquement
- **Signaux automatiques** : Création/modification de **DirectDebit** et **RecurringIncome** déclenche le traitement automatique

---

## 🏦 1. ACCOUNTS (Comptes Bancaires)

**Entité racine** : Représente un compte bancaire appartenant à un utilisateur.

**Base route:** `/api/accounts/`
**Modèle Django:** `Account`
**Relations:**
- Appartient à : `User` (propriétaire du compte)
- Contient : `Operation[]`, `DirectDebit[]`, `RecurringIncome[]`, `BudgetProjection[]`

**Champs principaux:**
- `id` (integer, auto) : Identifiant unique
- `user` (foreign key) : Propriétaire du compte
- `nom` (string, max 100 chars) : Nom du compte
- `solde` (decimal) : Solde actuel (mis à jour automatiquement)
- `created_by` (foreign key) : Utilisateur qui a créé le compte
- `created_at/updated_at` (datetime) : Timestamps automatiques

### 📋 Routes CRUD Standard

#### **GET** `/api/accounts/` - Liste des comptes
**Query Parameters:**
```json
{
  "user": "integer (optionnel)",
  "created_by": "integer (optionnel)",
  "search": "string (optionnel)",
  "ordering": "string (solde, created_at, updated_at)"
}
```

**Response:**
```json
[
  {
    "id": 1,
    "user_username": "john_doe",
    "nom": "Compte courant",
    "solde": "1250.75",
    "operations_count": 15,
    "updated_at": "2024-01-15T10:30:00Z"
  }
]
```

#### **POST** `/api/accounts/` - Créer un compte
**Body:**
```json
{
  "user": 1,
  "nom": "Nouveau compte",
  "solde": "1000.00"
}
```

**Response:**
```json
{
  "id": 2,
  "user": 1,
  "user_username": "john_doe",
  "nom": "Nouveau compte",
  "solde": "1000.00",
  "created_by": 1,
  "created_by_username": "john_doe",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

#### **GET** `/api/accounts/{id}/` - Détail d'un compte
**Response:** Structure identique au POST response

#### **PUT/PATCH** `/api/accounts/{id}/` - Modifier un compte
**Body:**
```json
{
  "nom": "Compte modifié",
  "solde": "1500.00"
}
```

#### **DELETE** `/api/accounts/{id}/` - Supprimer un compte
**Response:** `204 No Content` (si aucune opération liée)

### 🎯 Actions Personnalisées

#### **GET** `/api/accounts/{id}/operations/` - Opérations du compte
**Response:**
```json
{
  "account_id": 1,
  "account_username": "john_doe",
  "operations": [...],
  "total_operations": 15
}
```

#### **GET** `/api/accounts/{id}/statistics/` - Statistiques du compte
**Response:**
```json
{
  "account_id": 1,
  "account_username": "john_doe",
  "solde_actuel": 1250.75,
  "statistics": {
    "total_operations": 15,
    "total_montant_operations": 2500.50,
    "operations_30_jours": 5,
    "montant_30_jours": 300.00,
    "prélèvements_actifs": 3,
    "montant_prélèvements": -450.00
  }
}
```

#### **POST** `/api/accounts/{id}/adjust_balance/` - Ajuster le solde
**Body:**
```json
{
  "montant": "100.00",
  "raison": "Ajustement manuel"
}
```

**Response:**
```json
{
  "ajustement": 100.00,
  "ancien_solde": 1250.75,
  "nouveau_solde": 1350.75,
  "operation_created": true
}
```

#### **GET** `/api/accounts/summary/` - Résumé global des comptes
**Response:**
```json
{
  "total_comptes": 3,
  "total_solde": 3250.75,
  "comptes_positifs": 2,
  "comptes_negatifs": 1,
  "comptes": [
    {
      "id": 1,
      "nom": "Compte courant",
      "solde": "1250.75",
      "operations_count": 15
    }
  ]
}
```

#### **GET** `/api/accounts/global_overview/` - Vue d'ensemble complète
**Response:**
```json
{
  "summary": {
    "total_comptes": 3,
    "total_solde": 3250.75,
    "comptes_positifs": 2,
    "comptes_negatifs": 1
  },
  "recent_activity": {
    "operations_7_jours": 12,
    "operations_30_jours": 45,
    "prélèvements_actifs": 5,
    "revenus_actifs": 3
  },
  "alerts": {
    "comptes_negatifs": 1,
    "prélèvements_imminents": 2
  }
}
```

---

## 💰 2. OPERATIONS (Opérations Financières)

**Entité de base** : Représente une opération financière sur un compte.

**Base route:** `/api/operations/`
**Modèle Django:** `Operation`
**Relations:**
- Appartient à : `Account` (compte de référence)
- Créé par : `User` (utilisateur créateur)

**Champs principaux:**
- `id` (integer, auto) : Identifiant unique
- `compte_reference` (foreign key) : Compte concerné
- `montant` (decimal) : Montant de l'opération (positif = crédit, négatif = débit)
- `description` (string, max 255 chars) : Description de l'opération
- `date_operation` (date) : Date de l'opération (défaut: aujourd'hui)
- `created_by` (foreign key) : Utilisateur créateur
- `created_at/updated_at` (datetime) : Timestamps automatiques

### 📋 Routes CRUD Standard

#### **GET** `/api/operations/` - Liste des opérations
**Query Parameters:**
```json
{
  "compte_reference": "integer (optionnel)",
  "created_by": "integer (optionnel)",
  "search": "string (optionnel)",
  "ordering": "string (montant, created_at, updated_at, -created_at)",
  "page": "integer (optionnel)",
  "page_size": "integer (optionnel)"
}
```

**Response:**
```json
[
  {
    "id": 1,
    "compte_reference_username": "john_doe",
    "montant": "250.00",
    "description": "Salaire mensuel",
    "created_at": "2024-01-15T10:30:00.123Z"
  }
]
```

#### **POST** `/api/operations/` - Créer une opération
**Body:**
```json
{
  "compte_reference": 1,
  "montant": "250.00",
  "description": "Salaire mensuel",
  "date_operation": "2024-01-15"
}
```

**Response:**
```json
{
  "id": 1,
  "compte_reference": 1,
  "compte_reference_username": "john_doe",
  "montant": "250.00",
  "description": "Salaire mensuel",
  "date_operation": "2024-01-15",
  "created_by": 1,
  "created_by_username": "john_doe",
  "created_at": "2024-01-15T10:30:00.123Z",
  "updated_at": "2024-01-15T10:30:00.123Z"
}
```

#### **GET** `/api/operations/{id}/` - Détail d'une opération
**Response:** Structure identique au POST response

#### **PUT/PATCH** `/api/operations/{id}/` - Modifier une opération
**Body:**
```json
{
  "montant": "275.00",
  "description": "Salaire mensuel + prime"
}
```

#### **DELETE** `/api/operations/{id}/` - Supprimer une opération
**Response:** `204 No Content`

### 🎯 Actions Personnalisées

#### **GET** `/api/operations/statistics/` - Statistiques globales
**Response:**
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

#### **GET** `/api/operations/search/` - Recherche avancée
**Query Parameters:**
```json
{
  "q": "string (recherche textuelle)",
  "montant_min": "decimal (optionnel)",
  "montant_max": "decimal (optionnel)",
  "date_debut": "date (optionnel)",
  "date_fin": "date (optionnel)",
  "compte_reference": "integer (optionnel)"
}
```

#### **GET** `/api/operations/by_account/` - Opérations groupées par compte
**Response:**
```json
[
  {
    "account_id": 1,
    "account_username": "john_doe",
    "operations": [...],
    "total_operations": 15,
    "total_montant": 1250.75
  }
]
```

#### **POST** `/api/operations/bulk_create/` - Création en lot
**Body:**
```json
{
  "operations": [
    {
      "compte_reference": 1,
      "montant": "100.00",
      "description": "Opération 1"
    },
    {
      "compte_reference": 1,
      "montant": "-50.00",
      "description": "Opération 2"
    }
  ]
}
```

---

## 💳 3. DIRECT-DEBITS (Prélèvements Automatiques)

**Entité spécialisée** : Hérite d'Operation, représente un prélèvement automatique récurrent.

**Base route:** `/api/direct-debits/`
**Modèle Django:** `DirectDebit` (hérite de `Operation`)
**Relations:**
- Hérite de : `Operation`
- Appartient à : `Account` (compte de référence)

**Champs spécifiques:**
- `date_prelevement` (date) : Date du prochain prélèvement
- `frequence` (string) : Fréquence (Mensuel, Trimestriel, Semestriel, Annuel)
- `actif` (boolean) : Si le prélèvement est actif
- `echeance` (date, optionnel) : Date de fin du prélèvement

### 📋 Routes CRUD Standard

#### **GET** `/api/direct-debits/` - Liste des prélèvements
**Query Parameters:**
```json
{
  "compte_reference": "integer (optionnel)",
  "actif": "boolean (optionnel)",
  "frequence": "string (optionnel)",
  "search": "string (optionnel)",
  "ordering": "string (date_prelevement, montant, created_at)"
}
```

**Response:**
```json
[
  {
    "id": 1,
    "compte_reference_username": "john_doe",
    "montant": "50.00",
    "description": "Électricité",
    "date_prelevement": "2024-02-01",
    "frequence": "Mensuel",
    "actif": true,
    "echeance": "2024-12-31"
  }
]
```

#### **POST** `/api/direct-debits/` - Créer un prélèvement
**Body:**
```json
{
  "compte_reference": 1,
  "montant": "50.00",
  "description": "Électricité",
  "date_prelevement": "2024-02-01",
  "frequence": "Mensuel",
  "actif": true,
  "echeance": "2024-12-31"
}
```

### 🎯 Actions Personnalisées

#### **GET** `/api/direct-debits/active/` - Prélèvements actifs
**Response:**
```json
{
  "count": 5,
  "prélèvements": [...],
  "total_montant": 250.00
}
```

#### **GET** `/api/direct-debits/expired/` - Prélèvements expirés
**Response:**
```json
{
  "count": 2,
  "prélèvements": [...]
}
```

#### **GET** `/api/direct-debits/upcoming/` - Prélèvements à venir
**Response:**
```json
{
  "count": 3,
  "prélèvements": [...],
  "prochain_prélèvement": "2024-02-01"
}
```

#### **POST** `/api/direct-debits/{id}/extend/` - Prolonger l'échéance
**Body:**
```json
{
  "nouvelle_echeance": "2025-12-31"
}
```

#### **POST** `/api/direct-debits/bulk_status/` - Mise à jour groupée du statut
**Body:**
```json
{
  "prélèvements_ids": [1, 2, 3],
  "actif": false
}
```

#### **GET** `/api/direct-debits/statistics/` - Statistiques des prélèvements
**Response:**
```json
{
  "statistics": {
    "total_prélèvements": 8,
    "prélèvements_actifs": 5,
    "prélèvements_expirés": 3,
    "total_montant_actif": 350.00,
    "prélèvements_ce_mois": 2,
    "montant_ce_mois": 100.00
  }
}
```

#### **GET** `/api/direct-debits/dashboard/` - Tableau de bord
**Response:**
```json
{
  "summary": {
    "total_prélèvements": 8,
    "prélèvements_actifs": 5,
    "total_montant": 350.00
  },
  "upcoming": {
    "prochain_prélèvement": "2024-02-01",
    "prélèvements_7_jours": 2,
    "montant_7_jours": 100.00
  },
  "by_frequency": {
    "Mensuel": 3,
    "Trimestriel": 2,
    "Annuel": 3
  }
}
```

---

## 💰 4. RECURRING-INCOMES (Revenus Récurrents)

**Entité spécialisée** : Représente un revenu récurrent (salaire, allocation, etc.).

**Base route:** `/api/recurring-incomes/`
**Modèle Django:** `RecurringIncome`
**Relations:**
- Appartient à : `Account` (compte de référence)
- Créé par : `User` (utilisateur créateur)

**Champs principaux:**
- `id` (integer, auto) : Identifiant unique
- `compte_reference` (foreign key) : Compte de destination
- `montant` (decimal) : Montant du revenu
- `description` (string) : Description du revenu
- `type_revenu` (string) : Type (Salaire, Allocation, Prime, etc.)
- `date_premier_versement` (date) : Date du premier versement
- `frequence` (string) : Fréquence (Mensuel, Trimestriel, etc.)
- `actif` (boolean) : Si le revenu est actif
- `echeance` (date, optionnel) : Date de fin

### 📋 Routes CRUD Standard

#### **GET** `/api/recurring-incomes/` - Liste des revenus
**Query Parameters:**
```json
{
  "compte_reference": "integer (optionnel)",
  "actif": "boolean (optionnel)",
  "type_revenu": "string (optionnel)",
  "frequence": "string (optionnel)",
  "search": "string (optionnel)",
  "ordering": "string (date_premier_versement, montant, created_at)"
}
```

**Response:**
```json
[
  {
    "id": 1,
    "compte_reference_username": "john_doe",
    "montant": "2500.00",
    "description": "Salaire Net",
    "type_revenu": "Salaire",
    "date_premier_versement": "2024-01-25",
    "frequence": "Mensuel",
    "actif": true
  }
]
```

#### **POST** `/api/recurring-incomes/` - Créer un revenu
**Body:**
```json
{
  "compte_reference": 1,
  "montant": "2500.00",
  "description": "Salaire Net",
  "type_revenu": "Salaire",
  "date_premier_versement": "2024-01-25",
  "frequence": "Mensuel",
  "actif": true
}
```

### 🎯 Actions Personnalisées

#### **GET** `/api/recurring-incomes/active/` - Revenus actifs
**Response:**
```json
{
  "count": 3,
  "revenus": [...],
  "total_montant": 3500.00
}
```

#### **GET** `/api/recurring-incomes/upcoming/` - Revenus à venir
**Response:**
```json
{
  "count": 2,
  "revenus": [...],
  "prochain_versement": "2024-01-25"
}
```

#### **POST** `/api/recurring-incomes/bulk_create/` - Création en lot
**Body:**
```json
{
  "revenus": [
    {
      "compte_reference": 1,
      "montant": "2500.00",
      "description": "Salaire",
      "type_revenu": "Salaire",
      "date_premier_versement": "2024-01-25",
      "frequence": "Mensuel"
    }
  ]
}
```

#### **POST** `/api/recurring-incomes/{id}/toggle/` - Activer/Désactiver
**Response:**
```json
{
  "actif": false,
  "message": "Revenu désactivé avec succès"
}
```

#### **GET** `/api/recurring-incomes/statistics/` - Statistiques des revenus
**Response:**
```json
{
  "statistics": {
    "total_revenus": 5,
    "revenus_actifs": 3,
    "total_montant_actif": 3500.00,
    "revenus_ce_mois": 2,
    "montant_ce_mois": 2500.00,
    "by_type": {
      "Salaire": 2,
      "Allocation": 1,
      "Prime": 2
    }
  }
}
```

#### **GET** `/api/recurring-incomes/projections/` - Projections futures
**Query Parameters:**
```json
{
  "mois": "integer (optionnel, défaut: 6)"
}
```

**Response:**
```json
{
  "projections": [
    {
      "mois": "2024-01",
      "total_montant": 3500.00,
      "revenus_count": 3
    }
  ],
  "total_projection": 21000.00
}
```

---

## 📊 5. BUDGET-PROJECTIONS (Projections Budgétaires)

**Entité de projection** : Permet de calculer et sauvegarder des projections budgétaires.

**Base route:** `/api/budget-projections/`
**Modèle Django:** `BudgetProjection`
**Relations:**
- Appartient à : `Account` (compte de référence)
- Créé par : `User` (utilisateur créateur)

**Champs principaux:**
- `id` (integer, auto) : Identifiant unique
- `compte_reference` (foreign key) : Compte concerné
- `date_projection` (date) : Date de la projection
- `periode_projection` (integer) : Période en mois
- `projections_data` (json) : Données calculées de la projection
- `created_by` (foreign key) : Utilisateur créateur
- `created_at/updated_at` (datetime) : Timestamps automatiques

### 📋 Routes CRUD Standard

#### **GET** `/api/budget-projections/` - Liste des projections
**Query Parameters:**
```json
{
  "compte_reference": "integer (optionnel)",
  "date_projection": "date (optionnel)",
  "periode_projection": "integer (optionnel)",
  "ordering": "string (date_projection, created_at)"
}
```

**Response:**
```json
[
  {
    "id": 1,
    "compte_reference_username": "john_doe",
    "date_projection": "2024-01-15",
    "periode_projection": 6,
    "solde_final_projete": 3250.75,
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

#### **POST** `/api/budget-projections/` - Créer une projection
**Body:**
```json
{
  "compte_reference": 1,
  "date_projection": "2024-01-15",
  "periode_projection": 6
}
```

**Response:**
```json
{
  "id": 1,
  "compte_reference": 1,
  "compte_reference_username": "john_doe",
  "date_projection": "2024-01-15",
  "periode_projection": 6,
  "projections_data": {
    "solde_initial": 1250.75,
    "solde_final_projete": 3250.75,
    "evolution_mensuelle": [...],
    "prélèvements_projetes": [...],
    "revenus_projetes": [...]
  },
  "created_by": 1,
  "created_by_username": "john_doe",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### 🎯 Actions Personnalisées

#### **POST** `/api/budget-projections/calculate/` - Calcul temps réel
**Body:**
```json
{
  "compte_reference": 1,
  "periode_projection": 6,
  "date_debut": "2024-01-15"
}
```

**Response:**
```json
{
  "projection": {
    "solde_initial": 1250.75,
    "solde_final_projete": 3250.75,
    "evolution_mensuelle": [
      {
        "mois": "2024-01",
        "solde_debut": 1250.75,
        "solde_fin": 1450.75,
        "variation": 200.00
      }
    ],
    "prélèvements_projetes": [...],
    "revenus_projetes": [...]
  }
}
```

#### **GET** `/api/budget-projections/dashboard/` - Tableau de bord
**Response:**
```json
{
  "summary": {
    "total_projection": 3250.75,
    "projections_count": 3,
    "periode_moyenne": 6
  },
  "recent_projections": [...],
  "alerts": {
    "projections_negatives": 1,
    "projections_expirees": 0
  }
}
```

#### **GET** `/api/budget-projections/compare/` - Comparaison de scénarios
**Query Parameters:**
```json
{
  "projection_ids": "string (IDs séparés par des virgules)"
}
```

**Response:**
```json
{
  "comparison": [
    {
      "projection_id": 1,
      "solde_final": 3250.75,
      "variation": 2000.00
    }
  ]
}
```

---

## ⚙️ 6. AUTOMATED-TASKS (Tâches Automatiques) - **NOUVEAU**

**Entité de traçabilité** : Enregistre l'exécution des tâches automatiques (prélèvements, revenus).

**Base route:** `/api/automated-tasks/`
**Modèle Django:** `AutomatedTask`
**Relations:**
- Créé par : `User` (utilisateur déclencheur, peut être null pour tâches système)

**Champs principaux:**
- `id` (integer, auto) : Identifiant unique
- `task_type` (string) : Type de tâche (PAYMENT_PROCESSING, INCOME_PROCESSING, etc.)
- `execution_date` (datetime) : Date d'exécution
- `status` (string) : Statut (SUCCESS, ERROR, PARTIAL)
- `processed_count` (integer) : Nombre d'opérations traitées
- `error_message` (text, optionnel) : Message d'erreur
- `execution_duration` (decimal) : Durée d'exécution en secondes
- `details` (json) : Détails de l'exécution
- `created_by` (foreign key, optionnel) : Utilisateur déclencheur
- `created_at/updated_at` (datetime) : Timestamps automatiques

### 📋 Routes CRUD Standard

#### **GET** `/api/automated-tasks/` - Liste des tâches (Lecture seule)
**Query Parameters:**
```json
{
  "task_type": "string (optionnel)",
  "status": "string (optionnel)",
  "created_by": "integer (optionnel)",
  "search": "string (recherche dans error_message)",
  "ordering": "string (execution_date, processed_count, execution_duration)"
}
```

**Response:**
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

### 🎯 Actions Personnalisées

#### **GET** `/api/automated-tasks/statistics/` - Statistiques des tâches
**Response:**
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

#### **GET** `/api/automated-tasks/recent/` - Tâches récentes (24h)
**Response:**
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

#### **GET** `/api/automated-tasks/errors/` - Tâches en erreur
**Response:**
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

#### **GET** `/api/automated-tasks/summary/` - Résumé des tâches
**Response:**
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

## 🔄 Système de Traitement Automatique

### Signaux Automatiques

L'API intègre un système de signaux Django qui déclenche automatiquement le traitement des prélèvements et revenus :

#### **Traitement des Prélèvements**
- **Déclenchement** : Création ou modification d'un `DirectDebit`
- **Condition** : `date_prelevement <= date.today()` et `actif = true`
- **Action** : Création automatique d'une `Operation` de débit
- **Mise à jour** : Solde du compte et prochaine date de prélèvement
- **Traçabilité** : Enregistrement d'une `AutomatedTask`

#### **Traitement des Revenus**
- **Déclenchement** : Création ou modification d'un `RecurringIncome`
- **Condition** : `date_premier_versement <= date.today()` et `actif = true`
- **Action** : Création automatique d'une `Operation` de crédit
- **Mise à jour** : Solde du compte et prochaine date de versement
- **Traçabilité** : Enregistrement d'une `AutomatedTask`

### Scripts de Gestion

#### **Script Principal** : `manage_direct_debits.py`
```bash
# Traitement des prélèvements
python manage_direct_debits.py --payments

# Traitement des revenus
python manage_direct_debits.py --incomes

# Traitement complet
python manage_direct_debits.py --both
```

#### **Script de Test** : `test_automatic_operations.py`
```bash
# Tests des signaux automatiques
python test_automatic_operations.py
```

#### **Génération de Données** : `generate_test_data.py`
```bash
# Génération de données de test
python generate_test_data.py
```

---

## 🧪 Tests et Qualité

### Suite de Tests Automatisés

L'API inclut une suite complète de tests couvrant :

- **Tests Unitaires** : Modèles, serializers, validations
- **Tests d'Intégration** : ViewSets, endpoints, flux complets
- **Tests de Performance** : Temps de réponse, requêtes optimisées
- **Tests de Sécurité** : Authentification, permissions, isolation des données

### Outils de Test

#### **Fichier de Configuration** : `pytest.ini`
```ini
[tool:pytest]
DJANGO_SETTINGS_MODULE = core.settings
python_files = tests.py test_*.py *_tests.py
addopts = --reuse-db --nomigrations
```

#### **Script de Lancement** : `run_tests.py`
```bash
# Lancement des tests
python run_tests.py

# Tests avec couverture
python run_tests.py --coverage
```

---

## 📦 Dépendances et Installation

### Requirements
```
Django==5.2.3
djangorestframework==3.16.0
django-filter==24.1
PyJWT==2.10.1
python-dateutil==2.9.0
mysqlclient==2.2.7
mimesis==13.1.0
python-dotenv==1.1.1
```

### Installation
```bash
# Installation des dépendances
pip install -r requirements.txt

# Configuration de la base de données
python manage.py migrate

# Création d'un superuser
python manage.py createsuperuser

# Génération de données de test (optionnel)
python generate_test_data.py
```

---

## 🚀 Utilisation Avancée

### Traitement Automatique en Production

Pour un déploiement en production, il est recommandé de configurer un cron job pour le traitement automatique :

```bash
# Cron job pour le traitement quotidien (à 6h du matin)
0 6 * * * /usr/bin/python /path/to/mes-frais/manage_direct_debits.py --both
```

### Monitoring et Alertes

L'API fournit des endpoints de monitoring via les `AutomatedTask` :

- **Statistiques de performance** : Durée moyenne d'exécution
- **Taux de succès** : Pourcentage de tâches réussies
- **Alertes d'erreur** : Tâches en échec avec messages détaillés
- **Activité récente** : Tâches des dernières 24h/7 jours

### Optimisations

- **Requêtes optimisées** : Utilisation de `select_related` et `prefetch_related`
- **Pagination** : Toutes les listes sont paginées
- **Filtrage avancé** : Support de `django-filter`
- **Recherche textuelle** : Recherche dans les descriptions
- **Tri personnalisé** : Tri sur tous les champs pertinents

---

## 📝 Notes de Version

### Version Actuelle : 2.0.0

#### Nouvelles Fonctionnalités
- ✅ **Système de tâches automatiques** : Traçabilité complète des traitements
- ✅ **Signaux automatiques** : Traitement automatique des prélèvements et revenus
- ✅ **Scripts de gestion** : Outils pour le traitement manuel et les tests
- ✅ **Tests automatisés** : Suite de tests complète
- ✅ **Génération de données** : Script pour créer des données de test
- ✅ **Monitoring avancé** : Statistiques de performance et alertes

#### Améliorations
- 🔄 **Performance** : Optimisation des requêtes et de la pagination
- 🔒 **Sécurité** : Validation renforcée et isolation des données
- 📊 **Statistiques** : Endpoints de statistiques enrichis
- 🧪 **Tests** : Couverture de tests étendue
- 📚 **Documentation** : Documentation API complète et mise à jour

#### Corrections
- 🐛 **Validation** : Correction des validations de montants
- 🐛 **Signaux** : Amélioration de la gestion des erreurs
- 🐛 **Sérialisation** : Correction des formats de dates