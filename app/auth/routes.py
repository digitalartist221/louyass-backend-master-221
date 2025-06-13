from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserResponse, UserLogin
from .utils import hash_password, verify_password
from .jwt import create_access_token

router = APIRouter(prefix="/auth", tags=["Authentification"])

# --- Enregistrement d'un utilisateur ---
@router.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    # Vérifier si l'email est déjà utilisé
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email déjà utilisé.")
    
    # Vérifier si le CNI est déjà utilisé
    if user.cni and db.query(User).filter(User.cni == user.cni).first():
        raise HTTPException(status_code=400, detail="CNI déjà utilisé par un autre utilisateur.")

    # Hachage du mot de passe
    hashed_pwd = hash_password(user.password)

    # Création d'un nouvel utilisateur avec tous les champs
    user_data = user.model_dump()  # Utiliser model_dump() pour Pydantic v2
    user_data['password'] = hashed_pwd  # Ajouter le mot de passe haché
    new_user = User(**user_data)  # Créer l'utilisateur avec tous les champs du schéma

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# --- Connexion d'un utilisateur ---
@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    # Recherche de l'utilisateur par email
    db_user = db.query(User).filter(User.email == user.email).first()

    # Vérification des identifiants
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=400, detail="Identifiants incorrects.")

    # Création du token JWT avec l'ID de l'utilisateur
    token = create_access_token({
        "sub": db_user.email,
        "user_id": db_user.id  # Ajout de l'ID de l'utilisateur pour la validation
    })
    return {"access_token": token, "token_type": "bearer", "user": db_user }
