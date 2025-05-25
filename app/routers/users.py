from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app import models, schemas
from app.database import get_db

router = APIRouter(
    prefix="/users",  # Le préfixe de l'URL sera /users
    tags=["Utilisateurs"], # Tag pour la documentation Swagger UI
)

@router.post("/", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Crée un nouvel utilisateur.
    """
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cet email est déjà enregistré.")

    # Dans une vraie application, vous hacheriez le mot de passe ici
    # Pour la démonstration, nous le stockons tel quel (NON RECOMMANDÉ POUR LA PRODUCTION)
    hashed_password = user.password + "_hashed" # Remplacez par une fonction de hachage appropriée (ex: bcrypt)

    db_user = models.User(
        email=user.email,
        nom_utilisateur=user.nom_utilisateur,
        telephone=user.telephone,
        cni=user.cni,
        role=user.role,
        hashed_password=hashed_password # Stockez le mot de passe haché
    )
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un utilisateur avec cet email existe déjà."
        )


@router.get("/", response_model=List[schemas.UserResponse])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Récupère une liste d'utilisateurs.
    """
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users

@router.get("/{user_id}", response_model=schemas.UserResponse)
def read_user(user_id: int, db: Session = Depends(get_db)):
    """
    Récupère un utilisateur par son ID.
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouvé")
    return user

@router.put("/{user_id}", response_model=schemas.UserResponse)
def update_user(user_id: int, user_update: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Met à jour un utilisateur existant.
    Note: Cet exemple utilise UserCreate pour la mise à jour.
    Vous pourriez vouloir un schéma UserUpdate dédié sans mot de passe pour la sécurité.
    """
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouvé")

    # Vérifier si le nouvel email existe déjà pour un autre utilisateur
    if user_update.email != db_user.email:
        existing_user = db.query(models.User).filter(models.User.email == user_update.email).first()
        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cet email est déjà enregistré par un autre utilisateur.")

    # Mettre à jour les champs
    for field, value in user_update.model_dump(exclude_unset=True).items():
        if field == "password":
            # Hasher le nouveau mot de passe (encore une fois, utilisez une bibliothèque de hachage appropriée)
            setattr(db_user, "hashed_password", value + "_hashed")
        else:
            setattr(db_user, field, value)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """
    Supprime un utilisateur par son ID.
    """
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouvé")
    db.delete(db_user)
    db.commit()
    return # Pas de contenu en cas de suppression réussie