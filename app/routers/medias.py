from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db

router = APIRouter(
    prefix="/medias",
    tags=["Médias"],
)

@router.post("/", response_model=schemas.MediaResponse, status_code=status.HTTP_201_CREATED)
def create_media(media: schemas.MediaCreate, db: Session = Depends(get_db)):
    """
    Crée un nouveau média (photo/vidéo) pour une chambre.
    """
    db_chambre = db.query(models.Chambre).filter(models.Chambre.id == media.chambre_id).first()
    if not db_chambre:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Chambre avec l'ID {media.chambre_id} non trouvée.")

    db_media = models.Media(**media.model_dump())
    db.add(db_media)
    db.commit()
    db.refresh(db_media)
    return db_media

@router.get("/", response_model=List[schemas.MediaResponse])
def read_medias(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Récupère une liste de médias.
    """
    medias = db.query(models.Media).offset(skip).limit(limit).all()
    return medias

@router.get("/{media_id}", response_model=schemas.MediaResponse)
def read_media(media_id: int, db: Session = Depends(get_db)):
    """
    Récupère un média par son ID.
    """
    media = db.query(models.Media).filter(models.Media.id == media_id).first()
    if media is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Média non trouvé")
    return media

@router.put("/{media_id}", response_model=schemas.MediaResponse)
def update_media(media_id: int, media_update: schemas.MediaCreate, db: Session = Depends(get_db)):
    """
    Met à jour un média existant.
    """
    db_media = db.query(models.Media).filter(models.Media.id == media_id).first()
    if db_media is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Média non trouvé")

    if media_update.chambre_id != db_media.chambre_id:
        db_chambre = db.query(models.Chambre).filter(models.Chambre.id == media_update.chambre_id).first()
        if not db_chambre:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Chambre avec l'ID {media_update.chambre_id} non trouvée.")

    for field, value in media_update.model_dump(exclude_unset=True).items():
        setattr(db_media, field, value)

    db.add(db_media)
    db.commit()
    db.refresh(db_media)
    return db_media

@router.delete("/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_media(media_id: int, db: Session = Depends(get_db)):
    """
    Supprime un média par son ID.
    """
    db_media = db.query(models.Media).filter(models.Media.id == media_id).first()
    if db_media is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Média non trouvé")
    db.delete(db_media)
    db.commit()
    return