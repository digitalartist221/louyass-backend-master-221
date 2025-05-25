from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db

router = APIRouter(
    prefix="/problemes",
    tags=["Problèmes"],
)

@router.post("/", response_model=schemas.ProblemeResponse, status_code=status.HTTP_201_CREATED)
def create_probleme(probleme: schemas.ProblemeCreate, db: Session = Depends(get_db)):
    """
    Crée un nouveau problème.
    """
    db_contrat = db.query(models.Contrat).filter(models.Contrat.id == probleme.contrat_id).first()
    if not db_contrat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Contrat avec l'ID {probleme.contrat_id} non trouvé.")

    db_signaleur = db.query(models.User).filter(models.User.id == probleme.signale_par).first()
    if not db_signaleur:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Utilisateur signalant avec l'ID {probleme.signale_par} non trouvé.")

    db_probleme = models.Probleme(**probleme.model_dump())
    db.add(db_probleme)
    db.commit()
    db.refresh(db_probleme)
    return db_probleme

@router.get("/", response_model=List[schemas.ProblemeResponse])
def read_problemes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Récupère une liste de problèmes.
    """
    problemes = db.query(models.Probleme).offset(skip).limit(limit).all()
    return problemes

@router.get("/{probleme_id}", response_model=schemas.ProblemeResponse)
def read_probleme(probleme_id: int, db: Session = Depends(get_db)):
    """
    Récupère un problème par son ID.
    """
    probleme = db.query(models.Probleme).filter(models.Probleme.id == probleme_id).first()
    if probleme is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problème non trouvé")
    return probleme

@router.put("/{probleme_id}", response_model=schemas.ProblemeResponse)
def update_probleme(probleme_id: int, probleme_update: schemas.ProblemeCreate, db: Session = Depends(get_db)):
    """
    Met à jour un problème existant.
    """
    db_probleme = db.query(models.Probleme).filter(models.Probleme.id == probleme_id).first()
    if db_probleme is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problème non trouvé")

    if probleme_update.contrat_id != db_probleme.contrat_id:
        db_contrat = db.query(models.Contrat).filter(models.Contrat.id == probleme_update.contrat_id).first()
        if not db_contrat:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Contrat avec l'ID {probleme_update.contrat_id} non trouvé.")

    if probleme_update.signale_par != db_probleme.signale_par:
        db_signaleur = db.query(models.User).filter(models.User.id == probleme_update.signale_par).first()
        if not db_signaleur:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Utilisateur signalant avec l'ID {probleme_update.signale_par} non trouvé.")


    for field, value in probleme_update.model_dump(exclude_unset=True).items():
        setattr(db_probleme, field, value)

    db.add(db_probleme)
    db.commit()
    db.refresh(db_probleme)
    return db_probleme

@router.delete("/{probleme_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_probleme(probleme_id: int, db: Session = Depends(get_db)):
    """
    Supprime un problème par son ID.
    """
    db_probleme = db.query(models.Probleme).filter(models.Probleme.id == probleme_id).first()
    if db_probleme is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problème non trouvé")
    db.delete(db_probleme)
    db.commit()
    return