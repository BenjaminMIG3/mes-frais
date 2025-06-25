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

**Corps de la requête :**
```json
{
  "username": "user@example.com",
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
    "username": "user@example.com",
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
  "username": "nouveau@example.com",
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
    "username": "nouveau@example.com",
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
    "username": "user@example.com",
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