from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from app import models, schemas
from app.database import get_db

router = APIRouter(
    prefix="/rendez-vous",
    tags=["Rendez-vous"],
)

@router.post("/", response_model=schemas.RendezVousResponse, status_code=status.HTTP_201_CREATED)
def create_rendez_vous(rdv: schemas.RendezVousCreate, db: Session = Depends(get_db)):
    """
    Crée un nouveau rendez-vous.
    """
    db_locataire = db.query(models.User).filter(models.User.id == rdv.locataire_id).first()
    if not db_locataire:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Locataire avec l'ID {rdv.locataire_id} non trouvé.")

    db_chambre = db.query(models.Chambre).filter(models.Chambre.id == rdv.chambre_id).first()
    if not db_chambre:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Chambre avec l'ID {rdv.chambre_id} non trouvée.")

    db_rdv = models.RendezVous(**rdv.model_dump())
    db.add(db_rdv)
    db.commit()
    db.refresh(db_rdv)
    return db_rdv

@router.get("/", response_model=List[schemas.RendezVousResponse])
def read_rendez_vous(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Récupère une liste de rendez-vous.
    """
    rdvs = db.query(models.RendezVous).offset(skip).limit(limit).all()
    return rdvs

@router.get("/{rdv_id}", response_model=schemas.RendezVousResponse)
def read_rendez_vous_by_id(rdv_id: int, db: Session = Depends(get_db)):
    """
    Récupère un rendez-vous par son ID.
    """
    rdv = db.query(models.RendezVous).filter(models.RendezVous.id == rdv_id).first()
    if rdv is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rendez-vous non trouvé")
    return rdv

@router.put("/{rdv_id}", response_model=schemas.RendezVousResponse)
def update_rendez_vous(rdv_id: int, rdv_update: schemas.RendezVousCreate, db: Session = Depends(get_db)):
    """
    Met à jour un rendez-vous existant.
    """
    db_rdv = db.query(models.RendezVous).filter(models.RendezVous.id == rdv_id).first()
    if db_rdv is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rendez-vous non trouvé")

    if rdv_update.locataire_id != db_rdv.locataire_id:
        db_locataire = db.query(models.User).filter(models.User.id == rdv_update.locataire_id).first()
        if not db_locataire:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Locataire avec l'ID {rdv_update.locataire_id} non trouvé.")

    if rdv_update.chambre_id != db_rdv.chambre_id:
        db_chambre = db.query(models.Chambre).filter(models.Chambre.id == rdv_update.chambre_id).first()
        if not db_chambre:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Chambre avec l'ID {rdv_update.chambre_id} non trouvée.")

    for field, value in rdv_update.model_dump(exclude_unset=True).items():
        setattr(db_rdv, field, value)

    db.add(db_rdv)
    db.commit()
    db.refresh(db_rdv)
    return db_rdv

@router.delete("/{rdv_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rendez_vous(rdv_id: int, db: Session = Depends(get_db)):
    """
    Supprime un rendez-vous par son ID.
    """
    db_rdv = db.query(models.RendezVous).filter(models.RendezVous.id == rdv_id).first()
    if db_rdv is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rendez-vous non trouvé")
    db.delete(db_rdv)
    db.commit()
    return