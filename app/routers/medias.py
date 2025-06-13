from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import and_
import os
from pathlib import Path
from uuid import uuid4

from app import models, schemas
from app.database import get_db
from app.auth.utils import get_current_user

router = APIRouter(
    prefix="/medias",
    tags=["Médias"],
)

@router.post("/", response_model=schemas.MediaResponse, status_code=status.HTTP_201_CREATED)
def create_media(
    chambre_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Crée un nouveau média (photo/vidéo) pour une chambre.
    """
    # Vérifier que la chambre existe
    db_chambre = db.query(models.Chambre).filter(
        models.Chambre.id == chambre_id
    ).first()
    
    if not db_chambre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chambre avec l'ID {chambre_id} non trouvée."
        )

    # Générer un nom de fichier unique et créer le chemin
    file_extension = file.filename.split('.')[-1]
    unique_filename = f"{uuid4()}.{file_extension}"
    upload_path = Path("uploaded_media")
    upload_path.mkdir(exist_ok=True)
    file_path = upload_path / unique_filename

    # Sauvegarder le fichier
    try:
        with file_path.open("wb") as buffer:
            buffer.write(file.file.read())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du téléchargement du fichier: {str(e)}"
        )

    # Créer l'entrée dans la base de données
    db_media = models.Media(
        chambre_id=chambre_id,
        url=str(file_path),
        type=file.content_type,
        description=""  # Il manquait la description
    )
    
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
def update_media(
    media_id: int,
    media_update: schemas.MediaCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Met à jour un média existant.
    """
    db_media = db.query(models.Media).filter(models.Media.id == media_id).first()
    if db_media is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Média non trouvé")

    # Mettre à jour le fichier si nécessaire
    if 'file' in media_update:
        # Supprimer l'ancien fichier
        if os.path.exists(db_media.url):
            os.remove(db_media.url)
        
        # Sauvegarder le nouveau fichier
        file_extension = media_update.file.filename.split('.')[-1]
        unique_filename = f"{uuid4()}.{file_extension}"
        upload_path = Path("uploaded_media")
        upload_path.mkdir(exist_ok=True)
        file_path = upload_path / unique_filename

        try:
            with file_path.open("wb") as buffer:
                buffer.write(media_update.file.file.read())
            db_media.url = str(file_path)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erreur lors du téléchargement du fichier: {str(e)}"
            )

    # Mettre à jour les autres champs
    for field, value in media_update.model_dump(exclude_unset=True).items():
        if field != 'file':  # Ignorer le champ file qui a été traité séparément
            setattr(db_media, field, value)

    db.add(db_media)
    db.commit()
    db.refresh(db_media)
    return db_media

@router.delete("/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_media(
    media_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Supprime un média par son ID.
    """
    db_media = db.query(models.Media).filter(models.Media.id == media_id).first()
    if db_media is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Média non trouvé")

    # Supprimer le fichier physique
    if os.path.exists(db_media.url):
        os.remove(db_media.url)

    db.delete(db_media)
    db.commit()
    return