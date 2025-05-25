from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date, datetime

from app import models, schemas
from app.database import get_db

router = APIRouter(
    prefix="/paiements",
    tags=["Paiements"],
)

@router.post("/", response_model=schemas.PaiementResponse, status_code=status.HTTP_201_CREATED)
def create_paiement(paiement: schemas.PaiementCreate, db: Session = Depends(get_db)):
    """
    Crée un nouveau paiement.
    """
    db_contrat = db.query(models.Contrat).filter(models.Contrat.id == paiement.contrat_id).first()
    if not db_contrat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Contrat avec l'ID {paiement.contrat_id} non trouvé.")

    # Définir date_paiement si non fourni et statut est "payé"
    if paiement.statut == "payé" and paiement.date_paiement is None:
        paiement.date_paiement = datetime.now()

    db_paiement = models.Paiement(**paiement.model_dump())
    db.add(db_paiement)
    db.commit()
    db.refresh(db_paiement)
    return db_paiement

@router.get("/", response_model=List[schemas.PaiementResponse])
def read_paiements(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Récupère une liste de paiements.
    """
    paiements = db.query(models.Paiement).offset(skip).limit(limit).all()
    return paiements

@router.get("/{paiement_id}", response_model=schemas.PaiementResponse)
def read_paiement(paiement_id: int, db: Session = Depends(get_db)):
    """
    Récupère un paiement par son ID.
    """
    paiement = db.query(models.Paiement).filter(models.Paiement.id == paiement_id).first()
    if paiement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paiement non trouvé")
    return paiement

@router.put("/{paiement_id}", response_model=schemas.PaiementResponse)
def update_paiement(paiement_id: int, paiement_update: schemas.PaiementCreate, db: Session = Depends(get_db)):
    """
    Met à jour un paiement existant.
    """
    db_paiement = db.query(models.Paiement).filter(models.Paiement.id == paiement_id).first()
    if db_paiement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paiement non trouvé")

    if paiement_update.contrat_id != db_paiement.contrat_id:
        db_contrat = db.query(models.Contrat).filter(models.Contrat.id == paiement_update.contrat_id).first()
        if not db_contrat:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Contrat avec l'ID {paiement_update.contrat_id} non trouvé.")

    # Update date_paiement if status changes to "payé" and it's not already set
    if paiement_update.statut == "payé" and db_paiement.statut != "payé" and paiement_update.date_paiement is None:
        paiement_update.date_paiement = datetime.now()
    elif paiement_update.statut != "payé" and db_paiement.statut == "payé":
        # If status changes from paid to unpaid, consider clearing date_paiement
        paiement_update.date_paiement = None


    for field, value in paiement_update.model_dump(exclude_unset=True).items():
        setattr(db_paiement, field, value)

    db.add(db_paiement)
    db.commit()
    db.refresh(db_paiement)
    return db_paiement

@router.delete("/{paiement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_paiement(paiement_id: int, db: Session = Depends(get_db)):
    """
    Supprime un paiement par son ID.
    """
    db_paiement = db.query(models.Paiement).filter(models.Paiement.id == paiement_id).first()
    if db_paiement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paiement non trouvé")
    db.delete(db_paiement)
    db.commit()
    return