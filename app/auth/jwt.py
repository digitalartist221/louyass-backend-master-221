# app/auth/jwt.py

from jose import jwt, JWTError
from datetime import datetime, timedelta
from typing import Dict, Any
from fastapi import HTTPException, status # Importez status ici

# --- Configuration JWT (Source Unique de la Clé Secrète) ---
# Clé secrète à garder CONFIDENTIELLE.
# Cette clé DOIT être la même que celle utilisée pour ENCODER les tokens
# et celle utilisée pour les DÉCODER.
SECRET_KEY = "SallEtSene" # Remplacez par une chaîne de caractères aléatoire et complexe en production!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 # Le token expire après 30 minutes

# --- Fonctions de Création de Token ---

def create_access_token(data: dict):
    """
    Crée un token d'accès JWT avec une date d'expiration.
    Args:
        data (dict): Les données à inclure dans le payload du token (ex: {"user_id": 1, "sub": "user@example.com", "role": "proprietaire"}).
    Returns:
        str: Le token JWT encodé.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire}) # Ajoute la date d'expiration au payload
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- Fonctions de Décodage et de Validation de Token ---

def get_token_data(token: str) -> Dict[str, Any]:
    """
    Décode et valide un token JWT, gérant l'expiration et les erreurs de signature.
    Args:
        token (str): Le token JWT à valider.
    Returns:
        Dict: Le payload décodé du token si valide.
    Raises:
        HTTPException: Si le token est invalide, expiré, ou malformé.
    """
    # Message d'erreur standardisé pour les problèmes d'authentification
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Erreur lors de la validation des informations d'authentification: 401: Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Décoder le token en utilisant la clé secrète et l'algorithme
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Vérifier si la clé 'exp' (expiration) est présente dans le payload
        expire_timestamp = payload.get("exp")
        if expire_timestamp is None:
            raise credentials_exception # Le token est malformé ou ne contient pas d'expiration

        # Vérifier que le token n'est pas expiré
        # JWT stocke le temps d'expiration en timestamp UNIX
        if datetime.utcnow() > datetime.fromtimestamp(expire_timestamp):
            raise credentials_exception # Le token a expiré

        return payload
    except JWTError as e:
        # Erreur spécifique de JWT (signature invalide, token malformé, etc.)
        # Nous levons la même exception standardisée pour des raisons de sécurité et de cohérence
        raise credentials_exception from e
    except Exception as e:
        # Capture toutes les autres erreurs inattendues lors du décodage du token
        # Fournit un message générique pour éviter d'exposer des détails internes
        print(f"Erreur inattendue dans get_token_data: {e}") # Pour le débogage sur le serveur
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Une erreur interne est survenue lors de la validation du token.",
        )
