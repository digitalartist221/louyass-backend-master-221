import json
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, Float # Incluez Float pour le cast

from app import models, schemas
from app.database import get_db

router = APIRouter(
    prefix="/recherche",
    tags=["Recherche Publique"], # Tag pour la documentation Swagger UI
)

@router.get("/chambres/", response_model=List[schemas.RechercheResult])
def public_search_chambres(
    localisation: Optional[str] = Query(None, description="Recherche par ville/adresse de la maison"),
    prix_min: Optional[float] = Query(None, ge=0, description="Prix minimum de la chambre"),
    prix_max: Optional[float] = Query(None, ge=0, description="Prix maximum de la chambre"),
    type_chambre: Optional[str] = Query(None, description="Type de chambre ('simple', 'appartement', 'maison')"),
    capacite_min: Optional[int] = Query(None, ge=1, description="Capacité minimale de la chambre"),
    taille_min_m2: Optional[float] = Query(None, ge=0, description="Taille minimale de la chambre en m²"),
    search_query: Optional[str] = Query(None, description="Recherche par titre ou description de la chambre"),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter"),
    limit: int = Query(100, ge=1, le=200, description="Nombre maximum d'éléments à retourner")
):
    """
    Recherche publique de chambres disponibles.
    Permet de filtrer par localisation, prix, type, capacité et taille.
    """
    query = db.query(models.Chambre)\
              .options(
                  joinedload(models.Chambre.maison),
                  joinedload(models.Chambre.medias)
              )\
              .join(models.Maison)

    # Filter for available rooms only
    query = query.filter(models.Chambre.disponible == True)

    # Filter by general search query across multiple fields
    if search_query:
        query = query.filter(
            or_(
                models.Chambre.titre.ilike(f"%{search_query}%"),
                models.Chambre.description.ilike(f"%{search_query}%"),
                models.Maison.adresse.ilike(f"%{search_query}%"),
                models.Maison.ville.ilike(f"%{search_query}%")
            )
        )

    # Filter by location (address/city of the house)
    if localisation:
        query = query.filter(
            or_(
                models.Maison.adresse.ilike(f"%{localisation}%"),
                models.Maison.ville.ilike(f"%{localisation}%")
            )
        )

    # Filter by price range
    if prix_min is not None:
        query = query.filter(models.Chambre.prix >= prix_min)
    if prix_max is not None:
        query = query.filter(models.Chambre.prix <= prix_max)

    # Filter by room type
    if type_chambre:
        query = query.filter(models.Chambre.type == type_chambre)

    # Filter by minimum capacity
    if capacite_min is not None:
        query = query.filter(models.Chambre.capacite >= capacite_min)

    # Filter by minimum size (casting to Float for comparison)
    if taille_min_m2 is not None:
        query = query.filter(models.Chambre.taille.cast(Float) >= taille_min_m2)

    chambres = query.offset(skip).limit(limit).all()

    # Format the results into the RechercheResult schema
    results = []
    for chambre in chambres:
        media = None
        if chambre.medias and len(chambre.medias) > 0:
            # Get the first media URL and ensure it's a complete, absolute path
            media_url = chambre.medias[0].url
            # Prepend base URL only if it's a relative path.
            # Assuming api.baseURL on the frontend is correctly 'http://localhost:8000'
            # and media_url from DB is '/uploads/image.jpg'
            # If media_url from DB is already absolute, remove the condition.
            if not media_url.startswith('http://') and not media_url.startswith('https://'):
                 # This needs to match the actual base URL where your static files are served
                media = f"http://localhost:8000{media_url if media_url.startswith('/') else '/' + media_url}"
            else:
                media = media_url # It's already an absolute URL

        results.append(schemas.RechercheResult(
            id=chambre.id,
            type_bien=chambre.type,
            adresse=chambre.maison.adresse if chambre.maison else "N/A",
            prix=chambre.prix,
            description=chambre.description,
            details={
                "titre": chambre.titre, # Frontend expects 'titre'
                "ville": chambre.maison.ville if chambre.maison else "N/A",
                "superficie": chambre.maison.superficie if chambre.maison else None,
                "type": chambre.type,
                "meublee": chambre.meublee,
                "salle_de_bain": chambre.salle_de_bain,
                "disponible": chambre.disponible,
                "capacite": chambre.capacite,
                "taille": chambre.taille,
                "media": media, # This will be the absolute URL
                "maison_id": chambre.maison_id
            }
        ))

    return results




    