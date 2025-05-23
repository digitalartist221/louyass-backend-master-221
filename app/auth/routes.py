# app/auth/routes.py

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserResponse
from .utils import hash_password, verify_password
from .jwt import create_access_token

router = APIRouter(prefix="/auth", tags=["Authentification"])

# Route POST /auth/register - inscription
@router.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    # Vérifier si l'email existe déjà
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email déjà utilisé.")

    # Créer un nouvel utilisateur avec mot de passe haché
    hashed_pwd = hash_password(user.password)
    new_user = User(email=user.email, hashed_password=hashed_pwd)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# Route POST /auth/login - connexion
@router.post("/login")
def login(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()

    # Vérifier que l'utilisateur existe et que le mot de passe est bon
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Identifiants incorrects.")

    # Générer un token JWT pour cet utilisateur
    token = create_access_token({"sub": db_user.email})
    return {"access_token": token, "token_type": "bearer"}
