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

## 📋 Résumé des Endpoints (49 routes total)

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

#### **GET** `/api/accounts/summary/` - Résumé de tous les comptes
**Response:**
```json
{
  "total_comptes": 3,
  "total_solde": 5000.75,
  "comptes_negatifs": 1,
  "comptes_positifs": 2
}
```

#### **GET** `/api/accounts/global_overview/` - Vue d'ensemble globale
**Response:** Données complètes pour dashboard avec détails par compte

---

## 💰 2. OPERATIONS (Opérations Financières)

**Entité de transaction** : Représente une transaction financière sur un compte (crédit ou débit).

**Base route:** `/api/operations/`
**Modèle Django:** `Operation`
**Relations:**
- Appartient à : `Account` (compte de référence)
- Parent de : `DirectDebit` (prélèvement automatique)

**Champs principaux:**
- `id` (integer, auto) : Identifiant unique
- `compte_reference` (foreign key) : Compte concerné par l'opération
- `montant` (decimal) : Montant de l'opération (positif=crédit, négatif=débit)
- `description` (string, max 255 chars) : Description de l'opération
- `date_operation` (date, auto) : Date de l'opération
- `created_by` (foreign key) : Utilisateur qui a créé l'opération

**Logique métier :**
- Le solde du compte est automatiquement mis à jour lors des opérations CRUD
- Les montants peuvent être positifs (revenus) ou négatifs (dépenses)
- Validation : montant ne peut pas être zéro

### 📋 Routes CRUD Standard

#### **GET** `/api/operations/` - Liste des opérations
**Query Parameters:**
```json
{
  "compte_reference": "integer (optionnel)",
  "created_by": "integer (optionnel)",
  "search": "string (optionnel)",
  "ordering": "string (montant, created_at, updated_at)"
}
```

**Response:**
```json
[
  {
    "id": 1,
    "compte_reference_username": "john_doe",
    "montant": "250.00",
    "description": "Salaire",
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

#### **POST** `/api/operations/` - Créer une opération
**Body:**
```json
{
  "compte_reference": 1,
  "montant": "250.00",
  "description": "Virement reçu"
}
```

**Response:**
```json
{
  "id": 2,
  "compte_reference": 1,
  "compte_reference_username": "john_doe",
  "montant": "250.00",
  "description": "Virement reçu",
  "created_by": 1,
  "created_by_username": "john_doe",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

#### **PUT/PATCH** `/api/operations/{id}/` - Modifier une opération
**Body:** Structure identique au POST

#### **DELETE** `/api/operations/{id}/` - Supprimer une opération
**Response:** `204 No Content` (solde automatiquement ajusté)

### 🎯 Actions Personnalisées

#### **GET** `/api/operations/statistics/` - Statistiques des opérations
**Response:**
```json
{
  "statistics": {
    "total_operations": 50,
    "total_montant": 12500.75,
    "operations_30_jours": 15,
    "montant_30_jours": 3500.25,
    "operations_7_jours": 5,
    "montant_7_jours": 750.00,
    "operations_positives": 30,
    "montant_positif": 15000.00,
    "operations_negatives": 20,
    "montant_negatif": -2500.00
  }
}
```

#### **GET** `/api/operations/by_account/` - Opérations groupées par compte
**Response:**
```json
[
  {
    "account_id": 1,
    "account_username": "john_doe",
    "operations_count": 15,
    "total_montant": 2500.75,
    "operations": [...]
  }
]
```

#### **GET** `/api/operations/search/` - Recherche avancée
**Query Parameters:**
```json
{
  "q": "string (optionnel)",
  "min_montant": "decimal (optionnel)",
  "max_montant": "decimal (optionnel)",
  "date_debut": "date YYYY-MM-DD (optionnel)",
  "date_fin": "date YYYY-MM-DD (optionnel)"
}
```

#### **POST** `/api/operations/bulk_create/` - Créer plusieurs opérations
**Body:**
```json
{
  "operations": [
    {
      "compte_reference": 1,
      "montant": "100.00",
      "description": "Achat 1"
    },
    {
      "compte_reference": 1,
      "montant": "-50.00",
      "description": "Achat 2"
    }
  ]
}
```

---

## 🔄 3. DIRECT-DEBITS (Prélèvements Automatiques)

**Entité spécialisée** : Hérite d'Operation, représente des prélèvements récurrents automatiques.

**Base route:** `/api/direct-debits/`
**Modèle Django:** `DirectDebit` (hérite d'`Operation`)
**Relations:**
- Hérite de : `Operation` (toutes les propriétés + champs spécialisés)
- Appartient à : `Account` (via Operation.compte_reference)

**Champs spécialisés (en plus d'Operation):**
- `date_prelevement` (date) : Date du premier prélèvement
- `echeance` (date, nullable) : Date de fin des prélèvements (null = illimité)
- `frequence` (enum) : "Mensuel", "Trimestriel", "Annuel"
- `actif` (boolean, default=true) : Statut actif/inactif

**Logique métier :**
- Calculs automatiques des prochaines occurrences selon la fréquence
- Validation : date_prelevement et echeance ne peuvent pas être dans le passé
- Validation : echeance doit être >= date_prelevement
- Méthodes disponibles : `get_next_occurrence()`, `get_occurrences_until(date)`

### 📋 Routes CRUD Standard

#### **GET** `/api/direct-debits/` - Liste des prélèvements
**Query Parameters:**
```json
{
  "compte_reference": "integer (optionnel)",
  "created_by": "integer (optionnel)",
  "search": "string (optionnel)",
  "ordering": "string (montant, date_prelevement, echeance, created_at)"
}
```

**Response:**
```json
[
  {
    "id": 1,
    "compte_reference_username": "john_doe",
    "montant": "150.00",
    "description": "Abonnement internet",
    "date_prelevement": "2024-02-01",
    "echeance": null,
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

#### **POST** `/api/direct-debits/` - Créer un prélèvement
**Body:**
```json
{
  "compte_reference": 1,
  "montant": "150.00",
  "description": "Abonnement mensuel",
  "date_prelevement": "2024-02-01",
  "echeance": "2024-12-31",
  "frequence": "Mensuel"
}
```

**Response:**
```json
{
  "id": 2,
  "compte_reference": 1,
  "compte_reference_username": "john_doe",
  "montant": "150.00",
  "description": "Abonnement mensuel",
  "date_prelevement": "2024-02-01",
  "echeance": "2024-12-31",
  "created_by": 1,
  "created_by_username": "john_doe",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "is_active": true
}
```

**Choix pour `frequence`:**
- `"Mensuel"`
- `"Trimestriel"`
- `"Annuel"`

#### **PUT/PATCH** `/api/direct-debits/{id}/` - Modifier un prélèvement
**Body:** Structure identique au POST (sans compte_reference)

#### **DELETE** `/api/direct-debits/{id}/` - Supprimer un prélèvement
**Response:** `204 No Content`

### 🎯 Actions Personnalisées

#### **GET** `/api/direct-debits/active/` - Prélèvements actifs
**Response:**
```json
{
  "active_count": 5,
  "prélèvements_actifs": [...]
}
```

#### **GET** `/api/direct-debits/expired/` - Prélèvements expirés
**Response:**
```json
{
  "expired_count": 2,
  "prélèvements_expirés": [...]
}
```

#### **GET** `/api/direct-debits/upcoming/` - Prélèvements à venir (30 jours)
**Response:**
```json
{
  "upcoming_count": 3,
  "prélèvements_à_venir": [...]
}
```

#### **GET** `/api/direct-debits/statistics/` - Statistiques des prélèvements
**Response:**
```json
{
  "statistics": {
    "total_prélèvements": 10,
    "total_montant": 1500.00,
    "prélèvements_actifs": 8,
    "montant_actifs": 1200.00,
    "prélèvements_expirés": 2,
    "montant_expirés": 300.00,
    "prélèvements_ce_mois": 5,
    "montant_ce_mois": 750.00
  }
}
```

#### **GET** `/api/direct-debits/by_account/` - Prélèvements par compte
**Response:** Groupement par compte avec statistiques

#### **POST** `/api/direct-debits/{id}/extend/` - Prolonger l'échéance
**Body:**
```json
{
  "nouvelle_echeance": "2025-12-31"
}
```

#### **POST** `/api/direct-debits/bulk_update_status/` - Mise à jour en lot
**Body:**
```json
{
  "ids": [1, 2, 3],
  "actif": false
}
```

---

## 💵 4. RECURRING-INCOMES (Revenus Récurrents)

**Entité de revenu** : Représente des revenus récurrents (salaires, subventions, aides, etc.).

**Base route:** `/api/recurring-incomes/`
**Modèle Django:** `RecurringIncome`
**Relations:**
- Appartient à : `Account` (compte de destination)

**Champs principaux:**
- `id` (integer, auto) : Identifiant unique
- `compte_reference` (foreign key) : Compte de destination du revenu
- `montant` (decimal, positif) : Montant du revenu
- `description` (string, max 255 chars) : Description du revenu
- `date_premier_versement` (date) : Date du premier versement
- `date_fin` (date, nullable) : Date de fin des versements (null = illimité)
- `frequence` (enum) : "Hebdomadaire", "Mensuel", "Trimestriel", "Annuel"
- `actif` (boolean, default=true) : Statut actif/inactif
- `type_revenu` (enum) : "Salaire", "Subvention", "Aide", "Pension", "Loyer", "Autre"

**Logique métier :**
- Calculs automatiques des prochaines occurrences selon la fréquence
- Conversion automatique en équivalent mensuel pour les projections
- Validation : montant doit être positif
- Validation : dates cohérentes (date_fin >= date_premier_versement)
- Méthodes disponibles : `get_next_occurrence()`, `get_occurrences_until(date)`

### 📋 Routes CRUD Standard

#### **GET** `/api/recurring-incomes/` - Liste des revenus
**Query Parameters:**
```json
{
  "compte_reference": "integer (optionnel)",
  "type_revenu": "string (optionnel)",
  "frequence": "string (optionnel)",
  "actif": "boolean (optionnel)",
  "search": "string (optionnel)",
  "ordering": "string (montant, date_premier_versement, created_at)"
}
```

**Response:**
```json
[
  {
    "id": 1,
    "compte_reference_username": "john_doe",
    "montant": "2500.00",
    "description": "Salaire principal",
    "date_premier_versement": "2024-01-01",
    "date_fin": null,
    "frequence": "Mensuel",
    "type_revenu": "Salaire",
    "is_active": true,
    "next_occurrence": "2024-02-01",
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

#### **POST** `/api/recurring-incomes/` - Créer un revenu
**Body:**
```json
{
  "compte_reference": 1,
  "montant": "2500.00",
  "description": "Salaire mensuel",
  "date_premier_versement": "2024-02-01",
  "date_fin": null,
  "frequence": "Mensuel",
  "actif": true,
  "type_revenu": "Salaire"
}
```

**Choix pour `type_revenu`:**
- `"Salaire"`
- `"Subvention"`
- `"Aide"`
- `"Pension"`
- `"Loyer"`
- `"Autre"`

**Choix pour `frequence`:**
- `"Hebdomadaire"`
- `"Mensuel"`
- `"Trimestriel"`
- `"Annuel"`

**Response:**
```json
{
  "id": 2,
  "compte_reference": 1,
  "compte_reference_username": "john_doe",
  "montant": "2500.00",
  "description": "Salaire mensuel",
  "date_premier_versement": "2024-02-01",
  "date_fin": null,
  "frequence": "Mensuel",
  "actif": true,
  "type_revenu": "Salaire",
  "created_by": 1,
  "created_by_username": "john_doe",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "is_active": true,
  "next_occurrence": "2024-02-01"
}
```

#### **PUT/PATCH** `/api/recurring-incomes/{id}/` - Modifier un revenu
**Body:** Structure identique au POST (sans compte_reference)

#### **DELETE** `/api/recurring-incomes/{id}/` - Supprimer un revenu
**Response:** `204 No Content`

### 🎯 Actions Personnalisées

#### **GET** `/api/recurring-incomes/statistics/` - Statistiques des revenus
**Response:**
```json
{
  "statistics": {
    "total_revenus": 5,
    "revenus_actifs": 4,
    "montant_mensuel_equivalent": 3500.00,
    "montant_annuel_equivalent": 42000.00,
    "par_type": {
      "Salaire": {"count": 2, "montant_total": 5000.00},
      "Subvention": {"count": 1, "montant_total": 500.00}
    },
    "par_frequence": {
      "Mensuel": 3,
      "Trimestriel": 1
    }
  }
}
```

#### **GET** `/api/recurring-incomes/by_account/` - Revenus par compte
**Response:** Groupement par compte avec montants équivalents mensuels

#### **GET** `/api/recurring-incomes/active/` - Revenus actifs uniquement
**Response:**
```json
{
  "count": 4,
  "revenus": [...]
}
```

#### **GET** `/api/recurring-incomes/upcoming/` - Prochaines occurrences
**Query Parameters:**
```json
{
  "days": "integer (défaut: 30)"
}
```

**Response:**
```json
{
  "periode": "30 jours",
  "count": 3,
  "revenus": [
    {
      "id": 1,
      "description": "Salaire principal",
      "type_revenu": "Salaire",
      "montant": 2500.00,
      "date_occurrence": "2024-02-01",
      "jours_restants": 15,
      "compte": "Compte courant"
    }
  ]
}
```

#### **GET** `/api/recurring-incomes/projections/` - Projections de revenus
**Query Parameters:**
```json
{
  "mois": "integer (défaut: 12)"
}
```

#### **POST** `/api/recurring-incomes/{id}/toggle_active/` - Activer/désactiver
**Response:** Statut mis à jour

#### **POST** `/api/recurring-incomes/bulk_create/` - Créer plusieurs revenus
**Body:**
```json
{
  "revenus": [
    {
      "compte_reference": 1,
      "montant": "2500.00",
      "description": "Salaire",
      "type_revenu": "Salaire",
      "frequence": "Mensuel"
    }
  ]
}
```

---

## 📈 5. BUDGET-PROJECTIONS (Projections Budgétaires)

**Entité analytique** : Stocke et calcule des projections budgétaires sur plusieurs mois.

**Base route:** `/api/budget-projections/`
**Modèle Django:** `BudgetProjection`
**Relations:**
- Appartient à : `Account` (compte analysé)
- Utilise : `DirectDebit[]`, `RecurringIncome[]` (pour les calculs)

**Champs principaux:**
- `id` (integer, auto) : Identifiant unique
- `compte_reference` (foreign key) : Compte analysé
- `date_projection` (date) : Date de début de la projection
- `periode_projection` (integer, 1-60) : Nombre de mois à projeter
- `solde_initial` (decimal, auto) : Solde au moment de la création
- `projections_data` (JSON, auto) : Données calculées de la projection

**Logique métier complexe :**
- Calculs automatiques intégrant prélèvements et revenus récurrents
- Projections mensuelles avec évolution du solde
- Analyses statistiques (solde min/max, mois en négatif, etc.)
- Support de différents scénarios (optimiste, pessimiste, réaliste)
- Contrainte unique : (compte_reference, date_projection, periode_projection)

**Structure projections_data (JSON) :**
```json
{
  "compte_id": integer,
  "solde_initial": decimal,
  "projections_mensuelles": [
    {
      "mois": integer,
      "solde_debut": decimal,
      "solde_fin": decimal,
      "total_revenus": decimal,
      "total_prelevements": decimal,
      "transactions": [...]
    }
  ],
  "resume": {
    "revenus_totaux": decimal,
    "solde_minimum": decimal,
    "mois_solde_negatif": integer
  }
}
```

### 📋 Routes CRUD Standard

#### **GET** `/api/budget-projections/` - Liste des projections
**Query Parameters:**
```json
{
  "compte_reference": "integer (optionnel)",
  "periode_projection": "integer (optionnel)",
  "search": "string (optionnel)",
  "ordering": "string (date_projection, created_at)"
}
```

#### **POST** `/api/budget-projections/` - Créer une projection
**Body:**
```json
{
  "compte_reference": 1,
  "date_projection": "2024-02-01",
  "periode_projection": 12
}
```

**Response:** Projection créée avec calculs automatiques inclus

#### **GET** `/api/budget-projections/{id}/` - Détail d'une projection
**Response:** Projection complète avec toutes les données calculées

#### **PUT/PATCH** `/api/budget-projections/{id}/` - Modifier une projection
**Body:** Structure identique au POST

#### **DELETE** `/api/budget-projections/{id}/` - Supprimer une projection
**Response:** `204 No Content`

### 🎯 Actions Personnalisées

#### **POST** `/api/budget-projections/calculate/` - Calcul temps réel
**Body:**
```json
{
  "compte_reference": 1,
  "date_debut": "2024-02-01",
  "periode_mois": 6,
  "inclure_prelevements": true,
  "inclure_revenus": true
}
```

**Response:**
```json
{
  "compte_id": 1,
  "compte_nom": "Compte courant",
  "solde_initial": 1250.75,
  "solde_final_projete": 3500.25,
  "variation_totale": 2249.50,
  "date_debut": "2024-02-01",
  "date_fin": "2024-08-01",
  "periode_mois": 6,
  "projections_mensuelles": [
    {
      "mois": 1,
      "date_debut": "2024-02-01",
      "date_fin": "2024-02-29",
      "solde_debut": 1250.75,
      "solde_fin": 1600.75,
      "total_revenus": 2500.00,
      "total_prelevements": 2150.00,
      "variation": 350.00,
      "transactions": [...]
    }
  ],
  "resume": {
    "revenus_totaux": 15000.00,
    "prelevements_totaux": 12750.50,
    "solde_minimum": 850.25,
    "solde_maximum": 3500.25,
    "mois_solde_negatif": 0
  }
}
```

#### **GET** `/api/budget-projections/summary/` - Résumé budgétaire
**Query Parameters:**
```json
{
  "compte_id": "integer (optionnel)"
}
```

**Response:** Résumé complet ou par compte spécifique

#### **GET** `/api/budget-projections/dashboard/` - Tableau de bord
**Query Parameters:**
```json
{
  "periode_mois": "integer (défaut: 3, max: 60)"
}
```

**Response:**
```json
{
  "user_id": 1,
  "periode_projection": 3,
  "indicateurs_cles": {
    "solde_total_actuel": 5000.75,
    "nombre_comptes": 3,
    "revenus_mensuels_estimes": 3500.00,
    "prelevements_mensuels_estimes": 2750.00,
    "solde_mensuel_estime": 750.00,
    "projection_3_mois": 7250.75
  },
  "activite_recente": {
    "operations_7j": {...},
    "operations_30j": {...},
    "operations_90j": {...}
  },
  "repartition_comptes": [...],
  "alertes": [...]
}
```

#### **POST** `/api/budget-projections/quick_projection/` - Projection rapide
**Body:**
```json
{
  "compte_id": 1,
  "mois": 3,
  "scenario": "optimiste"
}
```

#### **GET** `/api/budget-projections/compare_scenarios/` - Comparaison de scénarios
**Query Parameters:**
```json
{
  "compte_id": "integer",
  "periode": "integer (défaut: 6)"
}
```

---

## 🚫 Codes d'Erreur Communs

### 400 Bad Request
```json
{
  "error": "Données invalides",
  "details": {
    "montant": ["Le montant ne peut pas être zéro."],
    "description": ["La description ne peut pas être vide."]
  }
}
```

### 401 Unauthorized
```json
{
  "error": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
  "error": "Vous ne pouvez pas accéder à ce compte"
}
```

### 404 Not Found
```json
{
  "error": "Compte non trouvé"
}
```

### 500 Internal Server Error
```json
{
  "error": "Erreur interne du serveur"
}
```

---

## 📝 Guide d'Implémentation pour LLM

### 🧠 Compréhension du Contexte Métier

**Domaine :** Application de gestion financière personnelle
**Objectif :** Permettre aux utilisateurs de suivre leurs finances, prévoir leurs budgets
**Public :** Particuliers gérant leurs comptes bancaires et budgets familiaux

**Workflow typique d'utilisation :**
1. Créer un ou plusieurs comptes bancaires (`/accounts/`)
2. Enregistrer des opérations financières (`/operations/`)
3. Configurer des prélèvements automatiques (`/direct-debits/`)
4. Définir des revenus récurrents (`/recurring-incomes/`)
5. Générer des projections budgétaires (`/budget-projections/`)

### 🔄 Logique de Mise à Jour Automatique

**Cascade de mise à jour des soldes :**
```
Operation CREATE/UPDATE/DELETE → Account.solde mis à jour automatiquement
DirectDebit (hérite Operation) → Même comportement
```

**Calculs en temps réel :**
- Projections budgétaires recalculées à chaque demande
- Statistiques agrégées dynamiquement
- Conversions de fréquences automatiques (hebdo → mensuel, etc.)

### 🎯 Patterns d'Usage Recommandés

**Pour un LLM assistant :**

1. **Consultation de données :**
   - Toujours commencer par `/accounts/` pour le contexte utilisateur
   - Utiliser `/statistics/` pour les résumés
   - Préférer `/summary/` et `/dashboard/` pour les vues d'ensemble

2. **Création de données :**
   - Valider l'existence du compte avant créer operations/prélèvements/revenus
   - Utiliser `/bulk_create/` pour les opérations multiples
   - Les IDs sont auto-générés, ne jamais les spécifier en création

3. **Recherche et filtrage :**
   - Utiliser les query parameters pour filtrer (`?compte_reference=1`)
   - `/search/` endpoints pour recherche textuelle
   - `/by_account/` pour grouper par compte

4. **Projections et analyses :**
   - `/calculate/` pour projections temporaires (pas de sauvegarde)
   - POST `/budget-projections/` pour sauvegarder des projections
   - `/dashboard/` pour aperçu complet de la situation financière

### ⚠️ Contraintes et Validations Critiques

**Contraintes métier absolues :**
- Les montants d'opération ne peuvent pas être zéro
- Les soldes de compte ne peuvent pas être négatifs à la création
- Les dates de prélèvement/échéance ne peuvent pas être dans le passé
- Un utilisateur ne peut accéder qu'à ses propres données (sauf staff)

**Validations automatiques :**
- Cohérence des dates (date_fin >= date_debut)
- Format des montants (decimal avec 2 décimales max)
- Unicité des projections (compte + date + période)

### 🏗️ Architecture Technique

**Framework :** Django REST Framework avec ViewSets
**Base de données :** PostgreSQL recommandé pour les calculs décimaux
**Héritage :** DirectDebit hérite d'Operation (table unique avec discriminateur)
**Permissions :** IsAuthenticated + filtrage par utilisateur dans get_queryset()

**Endpoints standards par modèle :**
- `GET /` : Liste (avec pagination)
- `POST /` : Création
- `GET /{id}/` : Détail
- `PUT/PATCH /{id}/` : Modification
- `DELETE /{id}/` : Suppression

**Actions personnalisées :**
- Pattern `@action(detail=True)` pour actions sur une instance
- Pattern `@action(detail=False)` pour actions sur la collection
- Suffixes courants : `/statistics/`, `/summary/`, `/active/`, `/upcoming/`

### 📊 Données de Test et Exemples

**Comptes typiques :**
- Compte courant (solde quotidien)
- Livret A (épargne)
- Compte joint (famille)

**Opérations courantes :**
- Salaire : +2500€ mensuel
- Loyer : -800€ mensuel  
- Courses : -300€ mensuel (variable)
- Essence : -200€ mensuel

**Prélèvements automatiques :**
- Abonnements : téléphone, internet, assurances
- Crédits : immobilier, voiture
- Utilities : électricité, gaz, eau

### 🚀 Optimisations de Performance

**Pour les LLMs :**
- Utiliser les endpoints `/summary/` plutôt que récupérer toutes les données
- Préférer les vues agrégées aux calculs côté client
- Limiter les appels API avec les filtres appropriés
- Utiliser `/dashboard/` pour les vues d'ensemble complètes

**Gestion de la pagination :**
```http
GET /api/operations/?limit=50&offset=0
GET /api/operations/?page=2  (si pagination par page activée)
```

Cette documentation est optimisée pour qu'un LLM comprenne parfaitement le contexte métier, les relations entre entités, et puisse utiliser l'API de manière efficace et cohérente. 