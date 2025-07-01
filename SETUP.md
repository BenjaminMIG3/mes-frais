# 🚀 Guide d'Installation et Lancement - Mes Frais

Ce guide explique comment installer, configurer et lancer l'application Mes Frais sur votre environnement local.

## 📋 Prérequis

### Système d'exploitation
- **macOS** (recommandé)
- **Linux** (Ubuntu/Debian)
- **Windows** (avec WSL recommandé)

### Logiciels requis
- **Python 3.8+** 
- **MySQL 8.0+**
- **Git**
- **pip** (gestionnaire de paquets Python)

### Vérification des prérequis
```bash
# Vérifier Python
python3 --version

# Vérifier MySQL
mysql --version

# Vérifier Git
git --version
```

## 🔧 Installation

### 1. Cloner le projet
```bash
git clone <url-du-repo>
cd mes-frais
```

### 2. Créer un environnement virtuel
```bash
# Créer l'environnement virtuel
python3 -m venv venv

# Activer l'environnement virtuel
# Sur macOS/Linux :
source venv/bin/activate
# Sur Windows :
venv\Scripts\activate
```

### 3. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 4. Configuration de la base de données

#### Créer la base de données MySQL
```sql
CREATE DATABASE mes_frais CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'mes_frais_user'@'localhost' IDENTIFIED BY 'votre_mot_de_passe';
GRANT ALL PRIVILEGES ON mes_frais.* TO 'mes_frais_user'@'localhost';
FLUSH PRIVILEGES;
```

#### Configurer les variables d'environnement
Créer un fichier `.env` à la racine du projet :
```bash
# Base de données
DB_NAME=mes_frais
DB_USER=mes_frais_user
DB_PASSWORD=votre_mot_de_passe
DB_HOST=localhost
DB_PORT=3306

# Django
SECRET_KEY=votre_cle_secrete_django
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# JWT
JWT_SECRET_KEY=votre_cle_jwt_secrete
JWT_ACCESS_TOKEN_LIFETIME=3600
JWT_REFRESH_TOKEN_LIFETIME=604800

# MongoDB (optionnel, pour les logs)
MONGODB_URI=mongodb://localhost:27017/mes_frais_logs
```

### 5. Configuration Django

#### Appliquer les migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

#### Créer un superutilisateur
```bash
python manage.py createsuperuser
```

#### Collecter les fichiers statiques
```bash
python manage.py collectstatic
```

## 🚀 Lancement du projet

### Mode développement
```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Lancer le serveur de développement
python manage.py runserver
```

L'application sera accessible à l'adresse : **http://127.0.0.1:8000**

### Mode production (avec Gunicorn)
```bash
# Installer Gunicorn si pas déjà fait
pip install gunicorn

# Lancer avec Gunicorn
gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

## 🧪 Tests et données de test

### Lancer les tests
```bash
# Tests unitaires
python manage.py test

# Tests avec pytest
pytest

# Tests avec couverture
pytest --cov=my_frais --cov=auth_api
```

### Générer des données de test
```bash
# Générer des données de test
python generate_test_data.py

# Générer des logs de test
python generate_test_logs.py
```

## 📊 Accès à l'interface d'administration

### Interface Django Admin
- **URL** : http://127.0.0.1:8000/admin/
- **Identifiants** : Utilisez les identifiants du superutilisateur créé

### API REST
- **Base URL** : http://127.0.0.1:8000/api/v1/
- **Documentation** : Consultez `API_DOCUMENTATION.md`

## 🔧 Scripts utiles

### Gestion des prélèvements automatiques
```bash
# Traiter tous les prélèvements à échéance
python manage_direct_debits.py
```

### Commandes Django personnalisées
```bash
# Lister les commandes disponibles
python manage.py help

# Exécuter une tâche automatique
python manage.py process_automatic_tasks
```

## 🐛 Dépannage

### Problèmes courants

#### Erreur de connexion à la base de données
```bash
# Vérifier que MySQL est démarré
sudo systemctl start mysql

# Vérifier les paramètres de connexion dans .env
```

#### Erreur de migration
```bash
# Réinitialiser les migrations
python manage.py migrate --fake-initial

# Ou supprimer et recréer la base
python manage.py flush
```

#### Problème de permissions
```bash
# Vérifier les permissions du dossier
chmod -R 755 .

# Vérifier les permissions de l'environnement virtuel
chmod -R 755 venv/
```

### Logs et debugging
```bash
# Activer le mode debug dans .env
DEBUG=True

# Consulter les logs Django
tail -f logs/django.log

# Consulter les logs MongoDB (si configuré)
mongo mes_frais_logs --eval "db.logs.find().sort({timestamp: -1}).limit(10)"
```

## 📁 Structure du projet

```
mes-frais/
├── core/                   # Configuration Django
├── my_frais/              # Application principale
│   ├── models.py          # Modèles de données
│   ├── viewsets/          # ViewSets API
│   ├── serializers/       # Sérialiseurs
│   └── services.py        # Services métier
├── auth_api/              # API d'authentification
├── templates/             # Templates HTML
├── requirements.txt       # Dépendances Python
├── manage.py             # Script de gestion Django
├── .env                  # Variables d'environnement
└── README.md             # Documentation fonctionnelle
```

## 🔄 Mise à jour du projet

```bash
# Récupérer les dernières modifications
git pull origin main

# Mettre à jour les dépendances
pip install -r requirements.txt

# Appliquer les nouvelles migrations
python manage.py migrate

# Redémarrer le serveur
python manage.py runserver
```

## 📞 Support

Pour toute question ou problème :
1. Consultez la documentation API (`API_DOCUMENTATION.md`)
2. Vérifiez les logs d'erreur
3. Consultez les issues GitHub du projet

---

**Note** : Ce guide est destiné au développement local. Pour la production, consultez la documentation de déploiement spécifique. 