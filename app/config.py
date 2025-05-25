# app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
import os

# Définir le répertoire de base du projet
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Settings(BaseSettings):
    """
    Classe de configuration pour l'application.
    Charge les variables d'environnement depuis un fichier .env.
    """
    model_config = SettingsConfigDict(
        env_file=os.path.join(BASE_DIR, '.env'), # Chemin vers le fichier .env
        extra='ignore' # Ignorer les variables non définies dans la classe
    )

    # Paramètres de base de l'application
    APP_NAME: str = "Louyass-221 Backend"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Paramètres de la base de données
    DATABASE_URL: str = Field(..., env="DATABASE_URL") # Doit être défini dans .env

    # Paramètres JWT
    SECRET_KEY: str = Field(..., env="SECRET_KEY") # Clé secrète pour le JWT
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30 # Durée de validité du token d'accès

    # Vous pouvez ajouter d'autres paramètres ici, par exemple pour les services externes, etc.

# Instanciez la classe Settings pour l'utiliser dans l'application
settings = Settings()

# Exemple d'utilisation
# print(settings.APP_NAME)  # Affiche le nom de l'application   