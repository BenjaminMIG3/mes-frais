# 📊 API Documentation - Mes Frais

Cette documentation présente une API REST complète pour la gestion de frais personnels et budgets familiaux. L'API permet de gérer des comptes bancaires, opérations financières, prélèvements automatiques, revenus récurrents et projections budgétaires.

## 🏗️ Architecture et Relations

### Modèle de Données Hiérarchique :
```
User (Utilisateur Django)
├── Account (Compte bancaire)
│   ├── Operation (Opération financière)
│   │   └── DirectDebit (Prélèvement - hérite d'Operation)
│   ├── RecurringIncome (Revenu récurrent)
│   └── BudgetProjection (Projection budgétaire)
```

### Relations Clés :
- **User → Account** : Un utilisateur peut avoir plusieurs comptes
- **Account → Operation** : Un compte a plusieurs opérations (1-N)
- **Operation → DirectDebit** : Les prélèvements sont des opérations spécialisées (héritage)
- **Account → RecurringIncome** : Un compte peut avoir plusieurs revenus récurrents (1-N)
- **Account → BudgetProjection** : Un compte peut avoir plusieurs projections (1-N)

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

### Actions les Plus Importantes pour un LLM :
1. **`GET /accounts/`** - Point d'entrée principal
2. **`GET /accounts/{id}/statistics/`** - Résumé d'un compte
3. **`GET /budget-projections/dashboard/`** - Vue d'ensemble complète
4. **`POST /budget-projections/calculate/`** - Projections temps réel
5. **`GET /operations/search/`** - Recherche avancée d'opérations

### Logique des Relations :
- **User** ← has many → **Account** ← has many → **Operation/DirectDebit/RecurringIncome/BudgetProjection**
- **DirectDebit** IS-A **Operation** (héritage)
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