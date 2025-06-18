from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload 
from sqlalchemy import and_

from app import models, schemas
from app.database import get_db
from app.auth.utils import get_current_user

router = APIRouter(
    prefix="/chambres", # Le préfixe de l'URL sera /chambres
    tags=["Chambres"],  # Tag pour la documentation Swagger UI
)

@router.post("/", response_model=schemas.ChambreResponse, status_code=status.HTTP_201_CREATED)
def create_chambre(
    chambre: schemas.ChambreCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Crée une nouvelle chambre pour la maison du propriétaire.
    """
    # Vérifier que l'utilisateur est propriétaire de la maison
    db_maison = db.query(models.Maison).filter(
        and_(
            models.Maison.id == chambre.maison_id,
            models.Maison.proprietaire_id == current_user.id
        )
    ).first()
    
    if not db_maison:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas autorisé à créer des chambres pour cette maison."
        )

    db_chambre = models.Chambre(**chambre.model_dump())
    db.add(db_chambre)
    db.commit()
    db.refresh(db_chambre)
    return db_chambre

@router.get("/mes-chambres", response_model=List[schemas.ChambreResponse])
def read_my_chambres(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Retrieve all chambers owned by the currently authenticated proprietor.
    """
    if current_user.role != "proprietaire":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les propriétaires peuvent consulter leurs chambres."
        )

    chambres = db.query(models.Chambre).options(
        joinedload(models.Chambre.maison).joinedload(models.Maison.proprietaire)
    ).join(models.Maison).filter(
        models.Maison.proprietaire_id == current_user.id
    ).all()

    # Adapt return based on your schemas.ChambreResponse structure
    return [
        schemas.ChambreResponse(
            id=chambre.id,
            maison_id=chambre.maison_id,
            titre=chambre.titre,
            description=chambre.description,
            taille=chambre.taille,
            type=chambre.type,
            meublee=chambre.meublee,
            prix=chambre.prix,
            capacite=chambre.capacite,
            salle_de_bain=chambre.salle_de_bain,
            disponible=chambre.disponible,
            cree_le=chambre.cree_le,
            maison=schemas.MaisonResponse(
                id=chambre.maison.id,
                proprietaire_id=chambre.maison.proprietaire_id,
                nom=chambre.maison.nom,
                adresse=chambre.maison.adresse,
                ville=chambre.maison.ville,
                superficie=chambre.maison.superficie,
                latitude=chambre.maison.latitude,
                longitude=chambre.maison.longitude,
                description=chambre.maison.description,
                cree_le=chambre.maison.cree_le
            ) if chambre.maison else None
        ) for chambre in chambres
    ]


@router.get("/{chambre_id}", response_model=schemas.ChambreResponse)
def read_chambre(
    chambre_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Retrieve a single chamber by its ID.
    Access controlled: only owner or admin (or locataire if appropriate context).
    """
    db_chambre = db.query(models.Chambre).options(
        joinedload(models.Chambre.maison).joinedload(models.Maison.proprietaire)
    ).filter(models.Chambre.id == chambre_id).first()

    if not db_chambre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chambre non trouvée"
        )

    # Permission check (similar to contracts/rendez-vous)
    if current_user.role == "proprietaire" and db_chambre.maison.proprietaire.id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas autorisé à consulter cette chambre."
        )
    # Add other role-based access if needed, e.g., locataire can view any publicly listed chambre

    return schemas.ChambreResponse( # Ensure this matches your schema and handles nested data
        id=db_chambre.id,
        maison_id=db_chambre.maison_id,
        titre=db_chambre.titre,
        description=db_chambre.description,
        taille=db_chambre.taille,
        type=db_chambre.type,
        meublee=db_chambre.meublee,
        prix=db_chambre.prix,
        capacite=db_chambre.capacite,
        salle_de_bain=db_chambre.salle_de_bain,
        disponible=db_chambre.disponible,
        cree_le=db_chambre.cree_le,
        maison=schemas.MaisonResponse(
            id=db_chambre.maison.id,
            proprietaire_id=db_chambre.maison.proprietaire_id,
            nom=db_chambre.maison.nom,
            adresse=db_chambre.maison.adresse,
            ville=db_chambre.maison.ville,
            superficie=db_chambre.maison.superficie,
            latitude=db_chambre.maison.latitude,
            longitude=db_chambre.maison.longitude,
            description=db_chambre.maison.description,
            cree_le=db_chambre.maison.cree_le
        ) if db_chambre.maison else None
    )



@router.get("/", response_model=List[schemas.ChambreResponse])
def read_chambres(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Récupère la liste des chambres appartenant au propriétaire.
    """
    chambres = db.query(models.Chambre).join(models.Maison).filter(models.Maison.proprietaire_id == current_user.id).offset(skip).limit(limit).all()
    
    return chambres
'''
@router.get("/{chambre_id}", response_model=schemas.ChambreResponse)
def read_chambre(chambre_id: int, db: Session = Depends(get_db)):
    """
    Récupère une chambre par son ID.
    """
    chambre = db.query(models.Chambre).filter(models.Chambre.id == chambre_id).first()
    if chambre is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chambre non trouvée")
    return chambre
'''
@router.put("/{chambre_id}", response_model=schemas.ChambreResponse)
def update_chambre(
    chambre_id: int, 
    chambre_update: schemas.ChambreCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Met à jour une chambre existante pour la maison du propriétaire.
    """
    # Vérifier que l'utilisateur est propriétaire de la chambre
    db_chambre = db.query(models.Chambre).filter(
        models.Chambre.id == chambre_id
    ).first()
    
    if db_chambre is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chambre non trouvée")
    
    # Vérifier que l'utilisateur est propriétaire de la maison
    if db_chambre.maison.proprietaire_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas autorisé à modifier cette chambre."
        )

    # Optionnel : Valider si maison_id est modifié et existe
    if chambre_update.maison_id != db_chambre.maison_id:
        db_maison = db.query(models.Maison).filter(
            and_(
                models.Maison.id == chambre_update.maison_id,
                models.Maison.proprietaire_id == current_user.id
            )
        ).first()
        if not db_maison:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'êtes pas autorisé à modifier cette chambre pour cette maison."
            )

    for field, value in chambre_update.model_dump(exclude_unset=True).items():
        setattr(db_chambre, field, value)

    db.add(db_chambre)
    db.commit()
    db.refresh(db_chambre)
    return db_chambre

@router.delete("/{chambre_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chambre(
    chambre_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Supprime une chambre pour la maison du propriétaire.
    """
    # Vérifier que l'utilisateur est propriétaire de la chambre
    db_chambre = db.query(models.Chambre).filter(
        models.Chambre.id == chambre_id
    ).first()
    
    if db_chambre is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chambre non trouvée")
    
    # Vérifier que l'utilisateur est propriétaire de la maison
    if db_chambre.maison.proprietaire_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas autorisé à supprimer cette chambre."
        )

    db.delete(db_chambre)
    db.commit()
    return