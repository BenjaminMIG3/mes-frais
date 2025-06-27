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

### 1.7 Interface utilisateur et expérience
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
Actifs | GET | **direct-debits/active/**
Expirés | GET | **direct-debits/expired/**
À venir (30 j) | GET | **direct-debits/upcoming/**
Statistiques | GET | **direct-debits/statistics/**
Vue par compte | GET | **direct-debits/by_account/**
Prolonger échéance | POST | **direct-debits/{id}/extend/**
Mise à jour groupée | POST | **direct-debits/bulk_update_status/**
Résumé global | GET | **direct-debits/summary/**

### 3.5 Revenus récurrents (`recurring-incomes`)
Opération | Méthode | Chemin
--- | --- | ---
Lister | GET | **recurring-incomes/**
Créer | POST | **recurring-incomes/**
Détail | GET | **recurring-incomes/{id}/**
Mettre à jour | PUT/PATCH | **recurring-incomes/{id}/**
Supprimer | DELETE | **recurring-incomes/{id}/**
Statistiques | GET | **recurring-incomes/statistics/**
Vue par compte | GET | **recurring-incomes/by_account/**
Actifs | GET | **recurring-incomes/active/**
À venir | GET | **recurring-incomes/upcoming/**
Projections | GET | **recurring-incomes/projections/**
Activation/Désactivation | POST | **recurring-incomes/{id}/toggle_active/**
Création en lot | POST | **recurring-incomes/bulk_create/**

### 3.6 Projections budgétaires (`budget-projections`)
Opération | Méthode | Chemin
--- | --- | ---
Lister | GET | **budget-projections/**
Créer | POST | **budget-projections/**
Détail | GET | **budget-projections/{id}/**
Mettre à jour | PUT/PATCH | **budget-projections/{id}/**
Supprimer | DELETE | **budget-projections/{id}/**
Calcul instantané | POST | **budget-projections/calculate/**
Résumé | GET | **budget-projections/summary/**
Dashboard | GET | **budget-projections/dashboard/**
Projection rapide (6 mois) | POST | **budget-projections/quick_projection/**
Comparaison de scénarios | GET | **budget-projections/compare_scenarios/**

### 3.7 Authentification et gestion des tokens

#### 3.7.1 Architecture d'authentification

L'API utilise un système d'authentification JWT (JSON Web Tokens) personnalisé avec deux types de tokens :

- **Access Token** : Durée de vie de 1 heure, utilisé pour les requêtes API
- **Refresh Token** : Durée de vie de 7 jours, utilisé pour renouveler l'access token

#### 3.7.2 Endpoints d'authentification détaillés

##### **POST /api/v1/auth/login/**
**Connexion utilisateur**

**Note :** Le champ `username` correspond au nom d'utilisateur (qui peut être différent de l'email). L'email est un champ séparé.

**Corps de la requête :**
```json
{
  "username": "nom_utilisateur",
  "password": "motdepasse123"
}
```

**Réponse réussie (200) :**
```json
{
  "message": "Connexion réussie",
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "username": "nom_utilisateur",
    "email": "user@example.com"
  }
}
```

**Erreurs possibles :**
- `400` : Données invalides ou email mal formaté
- `401` : Identifiants incorrects

##### **POST /api/v1/auth/register/**
**Inscription d'un nouvel utilisateur**

**Corps de la requête :**
```json
{
  "username": "nouvel_utilisateur",
  "password": "motdepasse123",
  "email": "nouveau@example.com"
}
```

**Réponse réussie (201) :**
```json
{
  "message": "Inscription réussie",
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 2,
    "username": "nouvel_utilisateur",
    "email": "nouveau@example.com"
  }
}
```

**Erreurs possibles :**
- `400` : Champs manquants
- `409` : Username ou email déjà utilisé

##### **POST /api/v1/auth/refresh_token/**
**Rafraîchissement du token d'accès**

**Corps de la requête :**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Réponse réussie (200) :**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "message": "Token rafraîchi avec succès"
}
```

**Erreurs possibles :**
- `400` : Refresh token manquant
- `401` : Refresh token invalide ou expiré

##### **POST /api/v1/auth/logout/**
**Déconnexion utilisateur**

**Réponse réussie (200) :**
```json
{
  "message": "Déconnexion réussie"
}
```

##### **GET /api/v1/auth/profile/**
**Récupération du profil utilisateur (protégé)**

**En-têtes requis :**
```
Authorization: Bearer <access_token>
```

**Réponse réussie (200) :**
```json
{
  "user": {
    "id": 1,
    "username": "nom_utilisateur",
    "email": "user@example.com",
    "first_name": "Prénom",
    "last_name": "Nom",
    "date_joined": "2024-01-15T10:30:00Z"
  }
}
```

#### 3.7.3 Structure des tokens JWT

##### **Access Token Payload :**
```json
{
  "user_id": 1,
  "username": "user@example.com",
  "exp": 1705312800,
  "iat": 1705309200,
  "type": "access",
  "jti": "1705309200000000"
}
```

##### **Refresh Token Payload :**
```json
{
  "user_id": 1,
  "exp": 1705914000,
  "iat": 1705309200,
  "type": "refresh",
  "jti": "1705309200000001"
}
```

#### 3.7.4 Gestion des erreurs d'authentification

##### **Codes d'erreur HTTP :**
- `401 Unauthorized` : Token manquant, invalide ou expiré
- `403 Forbidden` : Permissions insuffisantes
- `400 Bad Request` : Données de requête invalides

##### **Messages d'erreur typiques :**
```json
{
  "detail": "Token expiré"
}
```
```json
{
  "detail": "Token invalide"
}
```
```json
{
  "detail": "Utilisateur non trouvé"
}
```

#### 3.7.5 Sécurité et bonnes pratiques

##### **Côté client (React Native) :**
- Stockage sécurisé des tokens (Keychain iOS, Keystore Android)
- Rafraîchissement automatique avant expiration
- Gestion des erreurs 401 avec redirection vers login
- Nettoyage des tokens lors de la déconnexion

##### **Côté serveur :**
- Tokens signés avec `SECRET_KEY` Django
- Algorithmes de chiffrement : HS256
- Validation stricte des types de tokens
- Gestion des exceptions d'authentification

##### **Recommandations de sécurité :**
- Utilisation de HTTPS en production
- Rotation régulière des clés secrètes
- Monitoring des tentatives d'authentification
- Implémentation d'une blacklist de tokens (optionnel)

---

## 4. Structures des modèles

### 4.1 Modèle de base (BaseModel)
Tous les modèles héritent de cette classe abstraite qui fournit les champs de traçabilité :

```json
{
  "created_by": "integer (User ID)",
  "created_at": "datetime (auto)",
  "updated_at": "datetime (auto)"
}
```

### 4.2 Account (Compte bancaire)
```json
{
  "id": "integer (auto)",
  "user": "integer (User ID)",
  "nom": "string (max 100 chars, default: 'Compte bancaire')",
  "solde": "decimal (20,2, default: 0.00)",
  "created_by": "integer (User ID)",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### 4.3 Operation (Opération financière)
```json
{
  "id": "integer (auto)",
  "compte_reference": "integer (Account ID)",
  "montant": "decimal (20,2)",
  "description": "string (max 255 chars)",
  "date_operation": "date (auto)",
  "created_by": "integer (User ID)",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### 4.4 DirectDebit (Prélèvement automatique)
Hérite de `Operation` et ajoute les champs suivants :

```json
{
  "id": "integer (auto)",
  "compte_reference": "integer (Account ID)",
  "montant": "decimal (20,2)",
  "description": "string (max 255 chars)",
  "date_operation": "date (auto)",
  "date_prelevement": "date",
  "echeance": "date (nullable)",
  "frequence": "string (choices: 'Mensuel', 'Trimestriel', 'Annuel', default: 'Mensuel')",
  "actif": "boolean (default: true)",
  "created_by": "integer (User ID)",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### 4.5 RecurringIncome (Revenu récurrent)
```json
{
  "id": "integer (auto)",
  "compte_reference": "integer (Account ID)",
  "montant": "decimal (20,2)",
  "description": "string (max 255 chars)",
  "date_premier_versement": "date",
  "date_fin": "date (nullable)",
  "frequence": "string (choices: 'Hebdomadaire', 'Mensuel', 'Trimestriel', 'Annuel', default: 'Mensuel')",
  "actif": "boolean (default: true)",
  "type_revenu": "string (choices: 'Salaire', 'Subvention', 'Aide', 'Pension', 'Loyer', 'Autre', default: 'Salaire')",
  "created_by": "integer (User ID)",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### 4.6 BudgetProjection (Projection budgétaire)
```json
{
  "id": "integer (auto)",
  "compte_reference": "integer (Account ID)",
  "date_projection": "date",
  "periode_projection": "integer (nombre de mois)",
  "solde_initial": "decimal (20,2)",
  "projections_data": "json (données des projections)",
  "created_by": "integer (User ID)",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### 4.7 Contraintes et relations

**Contraintes d'unicité :**
- `BudgetProjection` : combinaison unique de `compte_reference`, `date_projection` et `periode_projection`

**Relations :**
- `Account` → `User` (Many-to-One)
- `Operation` → `Account` (Many-to-One)
- `DirectDebit` → `Account` (Many-to-One, hérite de `Operation`)
- `RecurringIncome` → `Account` (Many-to-One)
- `BudgetProjection` → `Account` (Many-to-One)

**Méthodes spéciales :**
- `DirectDebit.get_next_occurrence()` : calcule la prochaine occurrence
- `DirectDebit.get_occurrences_until()` : génère toutes les occurrences jusqu'à une date
- `RecurringIncome.get_next_occurrence()` : calcule la prochaine occurrence
- `RecurringIncome.get_occurrences_until()` : génère toutes les occurrences jusqu'à une date

---

## 5. Considérations supplémentaires
• Toutes les routes protégées nécessitent un **token d'accès JWT** dans l'en-tête `Authorization: Bearer <token>`.

• Les méthodes GET supportent la pagination, le filtrage, la recherche et l'ordering via les paramètres standards de Django REST Framework (page, page_size, search, ordering, etc.).

• Les formats de dates attendus sont au standard ISO 8601 (`YYYY-MM-DD`).

• Les montants sont exprimés en **euros** dans l'API.

### 5.1 Exigences techniques d'interface

#### **Gestion des thèmes**
- **Implémentation** : Utilisation d'un système de thèmes CSS variables ou d'un provider de thème (React Context, Redux, etc.)
- **Persistance** : Sauvegarde de la préférence dans le stockage local de l'appareil
- **Thèmes requis** :
  - **Mode clair** : Fond blanc, texte noir, couleurs d'accent modernes
  - **Mode sombre** : Fond sombre (#121212), texte clair, couleurs d'accent adaptées
- **Transition** : Animation fluide lors du basculement (300-500ms)
- **Cohérence** : Application du thème sur tous les écrans et composants

#### **Support multilingue (i18n)**
- **Framework recommandé** : React i18next ou équivalent
- **Langues prioritaires** :
  - Français (fr) - langue par défaut
  - Anglais (en) - langue secondaire
- **Détection automatique** : Utilisation de la langue système de l'appareil
- **Fallback** : Retour automatique au français si traduction manquante
- **Format des dates** : Adaptation selon la locale (DD/MM/YYYY pour FR, MM/DD/YYYY pour EN)
- **Format des montants** : Adaptation des séparateurs décimaux selon la locale
- **Direction du texte** : Support RTL pour futures langues

#### **Responsive Design**
- **Breakpoints recommandés** :
  - Mobile : < 768px
  - Tablette : 768px - 1024px
  - Desktop : > 1024px
- **Navigation** : Adaptation du menu selon la taille d'écran
- **Tableaux** : Scroll horizontal ou vue adaptée sur mobile
- **Formulaires** : Champs empilés sur mobile, disposition en colonnes sur desktop

#### **Accessibilité (WCAG 2.1 AA)**
- **Contraste** : Ratio minimum de 4.5:1 pour le texte normal
- **Navigation clavier** : Support complet de la navigation au clavier
- **Lecteurs d'écran** : Labels appropriés et structure sémantique
- **Taille de texte** : Support du zoom jusqu'à 200%
- **Couleurs** : Pas d'information véhiculée uniquement par la couleur

Ce document sera mis à jour au fur et à mesure des évolutions de l'API.

---

## 6. Endpoints de statistiques pour Dashboard

### 6.1 Vue d'ensemble des comptes

#### **GET /api/v1/accounts/summary/**
**Résumé basique des comptes de l'utilisateur**

**Réponse :**
```json
{
  "total_comptes": 3,
  "total_solde": 42488.44,
  "comptes_negatifs": 0,
  "comptes_positifs": 3
}
```

#### **GET /api/v1/accounts/global_overview/**
**Vue d'ensemble complète des comptes pour dashboard principal**

**Réponse :**
```json
{
  "resume": {
    "total_comptes": 3,
    "total_solde": 42488.44,
    "solde_moyen": 14162.81,
    "solde_maximum": 19944.49,
    "solde_minimum": 10610.55,
    "comptes_positifs": 3,
    "comptes_negatifs": 0,
    "total_operations": 87,
    "derniere_activite_globale": "2025-06-25T12:17:56.540252+00:00"
  },
  "repartition": {
    "excellent": 3,
    "bon": 0,
    "attention": 0,
    "critique": 0
  },
  "comptes": [
    {
      "id": 52,
      "nom": "PEL Banque Populaire",
      "solde": 19944.49,
      "status": "positif",
      "status_niveau": "excellent",
      "total_operations": 29,
      "operations_30j": 29,
      "variation_30j": 18944.49,
      "derniere_activite": "2025-06-25T12:17:56.540252+00:00",
      "prelevements_actifs": 2,
      "revenus_actifs": 1,
      "created_at": "2025-06-25T12:17:55.675585+00:00"
    }
  ],
  "alertes": {
    "comptes_critiques": 0,
    "comptes_attention": 0,
    "comptes_inactifs": 0,
    "necessite_attention": false
  }
}
```

### 6.2 Dashboard complet (recommandé)

#### **GET /api/v1/budget-projections/dashboard/**
**Tableau de bord complet avec toutes les métriques**

**Paramètres de requête optionnels :**
- `periode_mois` : Nombre de mois pour la projection (défaut: 3, max: 60)

**Réponse :**
```json
{
  "overview": {
    "comptes_count": 3,
    "solde_total": 42488.44,
    "revenus_mensuels": 5884.07,
    "prelevements_mensuels": 856.33,
    "solde_mensuel_estime": 5027.74,
    "status": "positif",
    "sante_financiere": "excellente"
  },
  "activite_recente": {
    "operations_7j": {
      "count": 87,
      "montant_total": 41488.44,
      "montant_positif": 48260.32,
      "montant_negatif": -6771.88
    },
    "operations_30j": { /* même structure */ },
    "operations_90j": { /* même structure */ }
  },
  "comptes": [
    {
      "id": 52,
      "nom": "PEL Banque Populaire",
      "solde": 19944.49,
      "nombre_operations": 29,
      "derniere_activite": "2025-06-25T12:17:56.540252+00:00",
      "status": "positif"
    }
  ],
  "alertes": {
    "niveau_urgence": "normal",
    "comptes_en_alerte": 0,
    "comptes_details": [],
    "messages_urgents": [],
    "prelevements_urgents": 0
  },
  "prochaines_echeances": {
    "prelevements_30j": {
      "count": 2,
      "montant_total": 856.33,
      "details": [
        {
          "id": 1,
          "description": "Électricité EDF",
          "montant": 85.50,
          "date": "2025-07-15",
          "jours_restants": 20,
          "compte": "Compte Courant",
          "frequence": "Mensuel",
          "type": "prelevement"
        }
      ]
    },
    "revenus_30j": {
      "count": 1,
      "montant_total": 2500.00,
      "details": [
        {
          "id": 1,
          "description": "Salaire Net",
          "type_revenu": "Salaire",
          "montant": 2500.00,
          "date": "2025-07-01",
          "jours_restants": 6,
          "compte": "Compte Courant",
          "frequence": "Mensuel",
          "type": "revenu"
        }
      ]
    }
  },
  "projections": {
    "periode_mois": 3,
    "tendance_mois": [
      {
        "mois": 1,
        "solde_projete": 47516.18,
        "variation": 5027.74
      },
      {
        "mois": 2,
        "solde_projete": 52543.92,
        "variation": 5027.74
      },
      {
        "mois": 3,
        "solde_projete": 57571.66,
        "variation": 5027.74
      }
    ],
    "capacite_epargne_mensuelle": 5027.74,
    "mois_avant_deficit": null
  },
  "metriques": {
    "ratio_revenus_prelevements": 6.87,
    "couverture_solde_mois": 49.64,
    "total_operations_mois": 87,
    "moyenne_operation": 476.98
  }
}
```

### 6.3 Statistiques par module

#### **GET /api/v1/operations/statistics/**
**Statistiques détaillées des opérations**

```json
{
  "statistics": {
    "total_operations": 87,
    "total_montant": 41488.44,
    "operations_30_jours": 87,
    "montant_30_jours": 41488.44,
    "operations_7_jours": 87,
    "montant_7_jours": 41488.44,
    "operations_positives": 58,
    "montant_positif": 48260.32,
    "operations_negatives": 29,
    "montant_negatif": -6771.88
  }
}
```

#### **GET /api/v1/direct-debits/statistics/**
**Statistiques des prélèvements automatiques**

```json
{
  "statistics": {
    "total_prélèvements": 7,
    "total_montant": 2569.00,
    "prélèvements_actifs": 7,
    "montant_actifs": 2569.00,
    "prélèvements_expirés": 0,
    "montant_expirés": 0.00,
    "prélèvements_ce_mois": 0,
    "montant_ce_mois": 0.00
  }
}
```

#### **GET /api/v1/recurring-incomes/statistics/**
**Statistiques des revenus récurrents**

```json
{
  "statistics": {
    "total_revenus": 4,
    "revenus_actifs": 4,
    "montant_mensuel_equivalent": 5884.07,
    "montant_annuel_equivalent": 70608.84,
    "par_type": {
      "Salaire": {"count": 2, "montant_total": 7218.41},
      "Subvention": {"count": 1, "montant_total": 205.68},
      "Aide": {"count": 1, "montant_total": 487.47},
      "Pension": {"count": 0, "montant_total": 0},
      "Loyer": {"count": 0, "montant_total": 0},
      "Autre": {"count": 0, "montant_total": 0}
    },
    "par_frequence": {
      "Hebdomadaire": 0,
      "Mensuel": 4,
      "Trimestriel": 0,
      "Annuel": 0
    }
  }
}
```

### 6.4 Projections et analyses détaillées

#### **POST /api/v1/budget-projections/calculate/**
**Calcul de projection complète en temps réel (sans sauvegarde)**

**Description :** Cet endpoint permet de calculer des projections budgétaires détaillées avec toutes les données mensuelles. Il est idéal pour l'analyse approfondie et les graphiques.

**Corps de la requête :**
```json
{
  "compte_reference": 52,
  "date_debut": "2025-01-01",
  "periode_mois": 6,
  "inclure_prelevements": true,
  "inclure_revenus": true
}
```

**Paramètres :**
- `compte_reference` : ID du compte (requis)
- `date_debut` : Date de début de la projection (optionnel, défaut: aujourd'hui)
- `periode_mois` : Nombre de mois à projeter (optionnel, défaut: 12, max: 60)
- `inclure_prelevements` : Inclure les prélèvements automatiques (optionnel, défaut: true)
- `inclure_revenus` : Inclure les revenus récurrents (optionnel, défaut: true)

**Réponse complète :**
```json
{
  "compte_id": 52,
  "compte_nom": "PEL Banque Populaire",
  "solde_initial": 19944.49,
  "solde_final_projete": 50110.93,
  "variation_totale": 30166.44,
  "date_debut": "2025-01-01",
  "date_fin": "2025-07-01",
  "periode_mois": 6,
  "projections_mensuelles": [
    {
      "mois": 1,
      "date_debut": "2025-01-01",
      "date_fin": "2025-01-31",
      "solde_debut": 19944.49,
      "solde_fin": 22644.49,
      "total_revenus": 3200.00,
      "total_prelevements": 500.00,
      "variation": 2700.00,
      "transactions": [
        {
          "date": "2025-01-01",
          "montant": 2500.00,
          "description": "Salaire Net",
          "type": "revenu"
        },
        {
          "date": "2025-01-15",
          "montant": -85.50,
          "description": "Électricité EDF",
          "type": "prelevement"
        }
      ]
    },
    {
      "mois": 2,
      "date_debut": "2025-02-01",
      "date_fin": "2025-02-28",
      "solde_debut": 22644.49,
      "solde_fin": 25344.49,
      "total_revenus": 3200.00,
      "total_prelevements": 500.00,
      "variation": 2700.00,
      "transactions": [...]
    }
  ],
  "resume": {
    "revenus_totaux": 19200.00,
    "prelevements_totaux": 3000.00,
    "solde_minimum": 19944.49,
    "solde_maximum": 50110.93,
    "mois_solde_negatif": 0
  }
}
```

**💡 Comment utiliser ces données :**

##### **Pour un graphique d'évolution du solde :**
```javascript
// Extraire les données pour un graphique
const chartData = response.projections_mensuelles.map(mois => ({
  periode: `${mois.date_debut.substring(0,7)}`, // "2025-01"
  solde: mois.solde_fin,
  revenus: mois.total_revenus,
  depenses: mois.total_prelevements
}));
```

##### **Pour détecter les mois critiques :**
```javascript
// Identifier les mois avec solde négatif
const moisCritiques = response.projections_mensuelles
  .filter(mois => mois.solde_fin < 0)
  .map(mois => ({
    periode: mois.mois,
    solde: mois.solde_fin,
    deficit: Math.abs(mois.solde_fin)
  }));
```

##### **Pour calculer la capacité d'épargne :**
```javascript
// Capacité d'épargne moyenne par mois
const capaciteEpargne = response.projections_mensuelles
  .map(mois => mois.variation)
  .reduce((sum, variation) => sum + variation, 0) / response.periode_mois;
```

#### **POST /api/v1/budget-projections/quick_projection/**
**Projection rapide paramétrable pour un compte**

**Description :** Version simplifiée pour obtenir rapidement les informations essentielles sans le détail mensuel.

**Corps de la requête :**
```json
{
  "compte_id": 52,
  "periode_mois": 6
}
```

**Note :** Le paramètre `periode_mois` est optionnel (défaut: 6, max: 60).

**Réponse :**
```json
{
  "compte": {
    "id": 52,
    "nom": "PEL Banque Populaire",
    "solde_actuel": 19944.49
  },
  "projection": {
    "periode_mois": 6,
    "solde_final": 50110.93,
    "variation_totale": 30166.44,
    "revenus_totaux": 35304.42,
    "prelevements_totaux": 5137.98,
    "solde_minimum": 19944.49,
    "mois_solde_negatif": 0
  },
  "alertes": {
    "deficit_prevu": false,
    "amelioration": true
  }
}
```

**💡 Utilisation recommandée :**
- **Cartes de résumé** : Utilisez `projection.solde_final` et `projection.variation_totale`
- **Indicateurs de santé** : Utilisez `alertes.deficit_prevu` et `projection.mois_solde_negatif`
- **Alertes visuelles** : Rouge si `deficit_prevu = true`, vert si `amelioration = true`

#### **GET /api/v1/budget-projections/dashboard/**
**Tableau de bord complet avec projections intégrées**

**Description :** Endpoint principal pour obtenir une vue d'ensemble complète avec projections, alertes et métriques.

**Paramètres de requête optionnels :**
- `periode_mois` : Nombre de mois pour la projection (défaut: 3, max: 60)

**Exemple d'usage :**
```
GET /api/v1/budget-projections/dashboard/?periode_mois=6
```

**Structure de réponse (partie projections) :**
```json
{
  "overview": {
    "solde_total": 42488.44,
    "revenus_mensuels": 5884.07,
    "prelevements_mensuels": 856.33,
    "solde_mensuel_estime": 5027.74,
    "sante_financiere": "excellente"
  },
  "projections": {
    "periode_mois": 6,
    "tendance_mois": [
      {
        "mois": 1,
        "solde_projete": 47516.18,
        "variation": 5027.74
      },
      {
        "mois": 2,
        "solde_projete": 52543.92,
        "variation": 5027.74
      },
      {
        "mois": 6,
        "solde_projete": 72654.40,
        "variation": 5027.74
      }
    ],
    "capacite_epargne_mensuelle": 5027.74,
    "mois_avant_deficit": null
  }
}
```

**💡 Utilisation du dashboard :**

##### **Graphique de tendance simple :**
```javascript
// Données pour graphique linéaire
const trendData = response.projections.tendance_mois.map((mois, index) => ({
  x: index + 1,
  y: mois.solde_projete,
  label: `Mois ${mois.mois}`
}));
```

##### **Indicateurs de performance :**
```javascript
// Calculs d'indicateurs
const performanceIndicators = {
  croissanceMoyenne: response.projections.capacite_epargne_mensuelle,
  croissanceTotale: response.projections.tendance_mois[response.projections.tendance_mois.length - 1].solde_projete - response.overview.solde_total,
  statusFinancier: response.overview.sante_financiere,
  alerteDeficit: response.projections.mois_avant_deficit !== null
};
```

#### **GET /api/v1/budget-projections/compare_scenarios/**
**Comparer différents scénarios de projection**

**Description :** Analyse comparative pour visualiser l'impact des revenus et prélèvements séparément.

**Paramètres de requête :**
- `compte_id` : ID du compte (requis)
- `periode_mois` : Nombre de mois pour la projection (optionnel, défaut: 12, max: 60)

**Exemple d'usage :**
```
GET /api/v1/budget-projections/compare_scenarios/?compte_id=52&periode_mois=12
```

**Réponse :**
```json
{
  "compte": {
    "id": 52,
    "nom": "PEL Banque Populaire",
    "solde_actuel": 19944.49
  },
  "periode_mois": 12,
  "scenarios": {
    "complet": {
      "nom": "Projection complète",
      "solde_final": 75000.50,
      "variation": 55056.01,
      "solde_minimum": 19944.49,
      "mois_deficit": 0
    },
    "prelevements_seulement": {
      "nom": "Prélèvements uniquement",
      "solde_final": 15000.25,
      "variation": -4944.24,
      "solde_minimum": 12500.00,
      "mois_deficit": 0
    },
    "revenus_seulement": {
      "nom": "Revenus uniquement",
      "solde_final": 90000.75,
      "variation": 70056.26,
      "solde_minimum": 19944.49,
      "mois_deficit": 0
    }
  }
}
```

**💡 Analyse des scénarios :**

##### **Impact des revenus vs prélèvements :**
```javascript
// Calculer l'impact de chaque composante
const impactAnalysis = {
  impactRevenus: response.scenarios.revenus_seulement.variation,
  impactPrelevements: Math.abs(response.scenarios.prelevements_seulement.variation),
  beneficeNet: response.scenarios.complet.variation,
  ratioPositivite: response.scenarios.revenus_seulement.variation / Math.abs(response.scenarios.prelevements_seulement.variation)
};
```

##### **Détection de risques :**
```javascript
// Identifier les risques financiers
const riskAssessment = {
  risqueDeficit: response.scenarios.prelevements_seulement.mois_deficit > 0,
  dependanceRevenus: response.scenarios.complet.solde_minimum <= response.compte.solde_actuel,
  margeSecurite: response.scenarios.complet.solde_minimum - response.compte.solde_actuel
};
```

### 6.5 Données regroupées

#### **GET /api/v1/operations/by_account/**
**Opérations groupées par compte**

#### **GET /api/v1/direct-debits/by_account/**
**Prélèvements groupés par compte**

#### **GET /api/v1/recurring-incomes/by_account/**
**Revenus récurrents groupés par compte**

### 6.6 Guide d'utilisation pratique des projections

#### **Stratégie d'endpoints selon le cas d'usage :**

##### **🏠 Dashboard principal d'accueil :**
```javascript
// Appel initial pour vue d'ensemble
GET /api/v1/budget-projections/dashboard/?periode_mois=3

// Utilisation recommandée :
- Afficher overview.solde_total en grand
- Graphique simple avec projections.tendance_mois
- Indicateur de santé : overview.sante_financiere
- Alertes rapides basées sur alertes.niveau_urgence
```

##### **📈 Page d'analyse détaillée :**
```javascript
// Pour graphiques et analyses poussées
POST /api/v1/budget-projections/calculate/
{
  "compte_reference": compte_id,
  "periode_mois": 12,
  "inclure_prelevements": true,
  "inclure_revenus": true
}

// Utilisation recommandée :
- Graphique détaillé avec projections_mensuelles[].solde_fin
- Table des transactions mensuelles
- Analyse des pics/creux avec resume.solde_minimum/maximum
```

##### **⚡ Résumés rapides (cartes, widgets) :**
```javascript
// Pour affichages compacts
POST /api/v1/budget-projections/quick_projection/
{
  "compte_id": compte_id,
  "periode_mois": 6
}

// Utilisation recommandée :
- Widget "Dans 6 mois : +X€"
- Indicateur progression avec projection.variation_totale
- Badge d'alerte si alertes.deficit_prevu
```

##### **🔍 Analyse comparative et diagnostics :**
```javascript
// Pour comprendre l'impact des revenus/charges
GET /api/v1/budget-projections/compare_scenarios/?compte_id=X&periode_mois=12

// Utilisation recommandée :
- Graphique comparatif des 3 scénarios
- Analyse "Que se passerait-il si..." 
- Conseils automatiques basés sur les ratios
```

#### **🎨 Recommandations d'interface :**

##### **Codes couleur suggérés :**
```css
/* Santé financière */
.excellente { color: #22c55e; } /* Vert foncé */
.bonne { color: #84cc16; }      /* Vert clair */
.fragile { color: #f59e0b; }    /* Orange */
.critique { color: #ef4444; }   /* Rouge */

/* Variations */
.variation-positive { color: #16a34a; }
.variation-negative { color: #dc2626; }
.variation-neutre { color: #6b7280; }
```

##### **Seuils d'alertes recommandés :**
```javascript
// Logique d'affichage des alertes
function getAlertLevel(projection) {
  if (projection.mois_solde_negatif > 0) return 'critique';
  if (projection.solde_minimum < 500) return 'attention'; 
  if (projection.variation_totale < 0) return 'vigilance';
  return 'normal';
}
```

#### **📱 Recommandations d'UX mobile :**

##### **Affichage adaptatif :**
- **Mobile** : Privilégier `quick_projection` pour la rapidité
- **Tablette** : Dashboard complet avec graphiques simplifiés  
- **Desktop** : Analyse détaillée avec `calculate` et comparaisons

##### **Mise en cache intelligente :**
```javascript
// Cache recommandé
const cacheStrategy = {
  dashboard: '5 minutes',      // Données temps réel
  quick_projection: '15 minutes', // Résumés fréquents
  calculate: '30 minutes',     // Analyses détaillées
  compare_scenarios: '1 heure' // Comparaisons statiques
};
```

#### **🔧 Exemples d'intégration complète :**

##### **Widget résumé compte :**
```javascript
async function loadAccountSummary(accountId) {
  const response = await fetch(`/api/v1/budget-projections/quick_projection/`, {
    method: 'POST',
    body: JSON.stringify({ compte_id: accountId, periode_mois: 3 })
  });
  
  const data = await response.json();
  
  return {
    currentBalance: data.compte.solde_actuel,
    projectedBalance: data.projection.solde_final,
    monthlyGrowth: data.projection.variation_totale / data.projection.periode_mois,
    isImproving: data.alertes.amelioration,
    hasDeficit: data.alertes.deficit_prevu
  };
}
```

##### **Graphique d'évolution :**
```javascript
async function loadEvolutionChart(accountId, months = 6) {
  const response = await fetch(`/api/v1/budget-projections/calculate/`, {
    method: 'POST',
    body: JSON.stringify({
      compte_reference: accountId,
      periode_mois: months
    })
  });
  
  const data = await response.json();
  
  return {
    labels: data.projections_mensuelles.map(m => m.date_debut.substring(5, 7)), // "01", "02"...
    datasets: [{
      label: 'Solde projeté',
      data: data.projections_mensuelles.map(m => m.solde_fin),
      borderColor: '#3b82f6',
      backgroundColor: '#dbeafe'
    }]
  };
}
```

#### **Indicateurs visuels suggérés :**

##### **Santé financière :**
- `excellente` : Vert foncé 🟢
- `bonne` : Vert clair 🟢
- `fragile` : Orange 🟠
- `critique` : Rouge 🔴

##### **Status des comptes :**
- `excellent` : Solde > 1000€
- `bon` : Solde > 0€
- `attention` : Solde > -500€
- `critique` : Solde ≤ -500€

##### **Niveau d'urgence :**
- `normal` : Pas d'action requise
- `attention` : Surveillance recommandée
- `critique` : Action immédiate requise 