from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date

from app import models, schemas
from app.database import get_db

router = APIRouter(
    prefix="/contrats",
    tags=["Contrats"],
)

@router.post("/", response_model=schemas.ContratResponse, status_code=status.HTTP_201_CREATED)
def create_contrat(contrat: schemas.ContratCreate, db: Session = Depends(get_db)):
    """
    Crée un nouveau contrat.
    """
    # Valider que le locataire existe
    db_locataire = db.query(models.User).filter(models.User.id == contrat.locataire_id).first()
    if not db_locataire:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Locataire avec l'ID {contrat.locataire_id} non trouvé.")

    # Valider que la chambre existe
    db_chambre = db.query(models.Chambre).filter(models.Chambre.id == contrat.chambre_id).first()
    if not db_chambre:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Chambre avec l'ID {contrat.chambre_id} non trouvée.")

    db_contrat = models.Contrat(**contrat.model_dump())
    db.add(db_contrat)
    db.commit()
    db.refresh(db_contrat)
    return db_contrat

@router.get("/", response_model=List[schemas.ContratResponse])
def read_contrats(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Récupère une liste de contrats.
    """
    contrats = db.query(models.Contrat).offset(skip).limit(limit).all()
    return contrats

@router.get("/{contrat_id}", response_model=schemas.ContratResponse)
def read_contrat(contrat_id: int, db: Session = Depends(get_db)):
    """
    Récupère un contrat par son ID.
    """
    contrat = db.query(models.Contrat).filter(models.Contrat.id == contrat_id).first()
    if contrat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrat non trouvé")
    return contrat

@router.put("/{contrat_id}", response_model=schemas.ContratResponse)
def update_contrat(contrat_id: int, contrat_update: schemas.ContratCreate, db: Session = Depends(get_db)):
    """
    Met à jour un contrat existant.
    """
    db_contrat = db.query(models.Contrat).filter(models.Contrat.id == contrat_id).first()
    if db_contrat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrat non trouvé")

    # Optional: Validate if locataire_id or chambre_id are changed and exist
    if contrat_update.locataire_id != db_contrat.locataire_id:
        db_locataire = db.query(models.User).filter(models.User.id == contrat_update.locataire_id).first()
        if not db_locataire:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Locataire avec l'ID {contrat_update.locataire_id} non trouvé.")

    if contrat_update.chambre_id != db_contrat.chambre_id:
        db_chambre = db.query(models.Chambre).filter(models.Chambre.id == contrat_update.chambre_id).first()
        if not db_chambre:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Chambre avec l'ID {contrat_update.chambre_id} non trouvée.")

    for field, value in contrat_update.model_dump(exclude_unset=True).items():
        setattr(db_contrat, field, value)

    db.add(db_contrat)
    db.commit()
    db.refresh(db_contrat)
    return db_contrat

@router.delete("/{contrat_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contrat(contrat_id: int, db: Session = Depends(get_db)):
    """
    Supprime un contrat par son ID.
    """
    db_contrat = db.query(models.Contrat).filter(models.Contrat.id == contrat_id).first()
    if db_contrat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrat non trouvé")
    db.delete(db_contrat)
    db.commit()
    return