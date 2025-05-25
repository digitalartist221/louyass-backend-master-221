# app/routers/maisons.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_ # Import for filtering

from app import models, schemas # Assuming schemas.py defines MaisonCreate, MaisonResponse, etc.
from app.database import get_db
# from app.auth.jwt import get_current_user # Uncomment if you need authentication

router = APIRouter(
    prefix="/maisons",  # Le préfixe de l'URL sera /maisons
    tags=["Maisons"],   # Tag pour la documentation Swagger UI
)

# --- Opération CRUD : Créer une Maison ---
@router.post("/", response_model=schemas.MaisonResponse, status_code=status.HTTP_201_CREATED)
def create_maison(
    maison: schemas.MaisonCreate,
    db: Session = Depends(get_db),
    # current_user: models.User = Depends(get_current_user) # Exemple pour l'authentification
):
    # Vérifier si le propriétaire_id existe (si l'utilisateur est authentifié, on pourrait utiliser current_user.id)
    proprietaire = db.query(models.User).filter(models.User.id == maison.proprietaire_id).first()
    if not proprietaire:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Propriétaire non trouvé."
        )

    db_maison = models.Maison(**maison.dict())
    db.add(db_maison)
    db.commit()
    db.refresh(db_maison)
    return db_maison

# --- Opération CRUD : Lire toutes les Maisons ---
@router.get("/", response_model=List[schemas.MaisonResponse])
def read_maisons(
    skip: int = 0,
    limit: int = 100,
    search_query: Optional[str] = None, # Pour la recherche par adresse ou description
    db: Session = Depends(get_db)
):
    query = db.query(models.Maison)

    if search_query:
        # Recherche insensible à la casse dans l'adresse ou la description
        query = query.filter(
            or_(
                models.Maison.adresse.ilike(f"%{search_query}%"),
                models.Maison.description.ilike(f"%{search_query}%")
            )
        )

    maisons = query.offset(skip).limit(limit).all()
    return maisons

# --- Opération CRUD : Lire une Maison par ID ---
@router.get("/{maison_id}", response_model=schemas.MaisonResponse)
def read_maison(maison_id: int, db: Session = Depends(get_db)):
    maison = db.query(models.Maison).filter(models.Maison.id == maison_id).first()
    if maison is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Maison non trouvée."
        )
    return maison

# --- Opération CRUD : Mettre à jour une Maison ---
@router.put("/{maison_id}", response_model=schemas.MaisonResponse)
def update_maison(
    maison_id: int,
    maison_update: schemas.MaisonCreate, # Utilisez MaisonCreate ou un MaisonUpdate si vous avez des champs optionnels
    db: Session = Depends(get_db),
    # current_user: models.User = Depends(get_current_user) # Exemple pour l'authentification
):
    db_maison = db.query(models.Maison).filter(models.Maison.id == maison_id).first()
    if db_maison is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Maison non trouvée."
        )

    # Assurez-vous que seul le propriétaire peut modifier sa maison
    # if db_maison.proprietaire_id != current_user.id:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Vous n'êtes pas autorisé à modifier cette maison."
    #     )

    # Mettre à jour les champs
    for key, value in maison_update.dict(exclude_unset=True).items():
        setattr(db_maison, key, value)

    db.add(db_maison)
    db.commit()
    db.refresh(db_maison)
    return db_maison

# --- Opération CRUD : Supprimer une Maison ---
@router.delete("/{maison_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_maison(
    maison_id: int,
    db: Session = Depends(get_db),
    # current_user: models.User = Depends(get_current_user) # Exemple pour l'authentification
):
    db_maison = db.query(models.Maison).filter(models.Maison.id == maison_id).first()
    if db_maison is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Maison non trouvée."
        )

    # Assurez-vous que seul le propriétaire peut supprimer sa maison
    # if db_maison.proprietaire_id != current_user.id:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Vous n'êtes pas autorisé à supprimer cette maison."
    #     )

    db.delete(db_maison)
    db.commit()
    return {"message": "Maison supprimée avec succès."}