from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db

router = APIRouter(
    prefix="/chambres", # Le préfixe de l'URL sera /chambres
    tags=["Chambres"],  # Tag pour la documentation Swagger UI
)

@router.post("/", response_model=schemas.ChambreResponse, status_code=status.HTTP_201_CREATED)
def create_chambre(chambre: schemas.ChambreCreate, db: Session = Depends(get_db)):
    """
    Crée une nouvelle chambre.
    """
    # Optionnel : Valider que maison_id existe
    db_maison = db.query(models.Maison).filter(models.Maison.id == chambre.maison_id).first()
    if not db_maison:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Maison avec l'ID {chambre.maison_id} non trouvée.")

    db_chambre = models.Chambre(**chambre.model_dump())
    db.add(db_chambre)
    db.commit()
    db.refresh(db_chambre)
    return db_chambre

@router.get("/", response_model=List[schemas.ChambreResponse])
def read_chambres(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Récupère une liste de chambres.
    """
    chambres = db.query(models.Chambre).offset(skip).limit(limit).all()
    return chambres

@router.get("/{chambre_id}", response_model=schemas.ChambreResponse)
def read_chambre(chambre_id: int, db: Session = Depends(get_db)):
    """
    Récupère une chambre par son ID.
    """
    chambre = db.query(models.Chambre).filter(models.Chambre.id == chambre_id).first()
    if chambre is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chambre non trouvée")
    return chambre

@router.put("/{chambre_id}", response_model=schemas.ChambreResponse)
def update_chambre(chambre_id: int, chambre_update: schemas.ChambreCreate, db: Session = Depends(get_db)):
    """
    Met à jour une chambre existante.
    """
    db_chambre = db.query(models.Chambre).filter(models.Chambre.id == chambre_id).first()
    if db_chambre is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chambre non trouvée")

    # Optionnel : Valider si maison_id est modifié et existe
    if chambre_update.maison_id != db_chambre.maison_id:
        db_maison = db.query(models.Maison).filter(models.Maison.id == chambre_update.maison_id).first()
        if not db_maison:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Maison avec l'ID {chambre_update.maison_id} non trouvée.")

    for field, value in chambre_update.model_dump(exclude_unset=True).items():
        setattr(db_chambre, field, value)

    db.add(db_chambre)
    db.commit()
    db.refresh(db_chambre)
    return db_chambre

@router.delete("/{chambre_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chambre(chambre_id: int, db: Session = Depends(get_db)):
    """
    Supprime une chambre par son ID.
    """
    db_chambre = db.query(models.Chambre).filter(models.Chambre.id == chambre_id).first()
    if db_chambre is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chambre non trouvée")
    db.delete(db_chambre)
    db.commit()
    return