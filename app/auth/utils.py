# app/auth/utils.py

from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
# Importez get_token_data pour la validation et le décodage du token.
# SECRET_KEY n'est plus définie ici, elle est gérée dans jwt.py
from app.auth.jwt import get_token_data 

# Contexte pour hachage avec l'algorithme bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
# Le tokenUrl doit correspondre à votre endpoint FastAPI de connexion (par exemple, /auth/login).
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login") 

# Hacher un mot de passe en clair
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# Vérifier un mot de passe contre son haché
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Dépendance FastAPI pour obtenir l'utilisateur actuel à partir du token
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    # Définir l'exception à lever si les informations d'identification sont invalides.
    # Ce message correspond à celui levé par get_token_data en cas d'échec de validation JWT.
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Erreur lors de la validation des informations d'authentification: 401: Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Utiliser la fonction centralisée get_token_data pour décoder et valider le token.
        # Cette fonction gère déjà les JWTError et les vérifications d'expiration.
        payload = get_token_data(token) 
        
        # Récupérer l'ID de l'utilisateur du payload du token.
        # TRÈS IMPORTANT : Lors de la CRÉATION du token dans votre endpoint de connexion
        # (ex: /auth/login), l'ID de l'utilisateur DOIT être stocké sous la clé 'user_id'
        # dans le dictionnaire de données passé à create_access_token.
        # Exemple: create_access_token(data={"user_id": user.id, "sub": user.email, ...})
        user_id: int = payload.get("user_id") 
        
        if user_id is None:
            # Si 'user_id' est manquant dans le payload (même après décodage réussi),
            # cela indique un payload malformé du point de vue de l'application.
            raise credentials_exception
            
        # Récupérer l'utilisateur depuis la base de données en utilisant l'ID extrait du token
        user = db.query(models.User).filter(models.User.id == user_id).first()
        
        if user is None:
            # Si un utilisateur n'est pas trouvé avec cet ID (ex: utilisateur supprimé),
            # c'est aussi un échec de validation des credentials.
            raise credentials_exception 
            
        # Retourner l'objet utilisateur SQLAlchemy.
        # FastAPI et Pydantic se chargeront de la sérialisation vers le modèle de réponse si nécessaire.
        return user
    except HTTPException:
        # Capture et relève les HTTPExceptions qui proviennent directement de get_token_data
        # (c'est-à-dire les erreurs 401 liées au token lui-même).
        raise
    except Exception as e:
        # Capture toutes les autres erreurs inattendues qui pourraient survenir.
        # C'est une mesure de sécurité pour ne pas exposer des détails sensibles
        # et fournir un message générique en cas de problème interne.
        print(f"Erreur inattendue dans get_current_user: {e}") # Journalisez l'erreur pour le débogage
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Une erreur interne est survenue lors de l'authentification.",
        )
