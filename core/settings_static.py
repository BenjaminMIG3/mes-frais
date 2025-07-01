# Configuration spécifique pour la collecte des fichiers statiques
# Utilise SQLite pour éviter les dépendances avec MySQL lors du build

from .settings import *

# Override de la configuration de base de données pour utiliser SQLite
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Désactiver MongoDB pour le build statique
MONGODB_CONFIG = {
    'host': 'localhost',
    'port': 27017,
    'database': 'temp',
    'username': '',
    'password': '',
    'auth_source': '',
}

# Optimisations pour le build
DEBUG = False
ALLOWED_HOSTS = ['*'] 