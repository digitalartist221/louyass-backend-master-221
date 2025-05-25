from typing import List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_ # Pour les conditions OR dans la requête

from app import models, schemas
from app.database import get_db

router = APIRouter(
    prefix="/recherche",
    tags=["Recherche"],
)
@router.get("/maisons-et-chambres/", response_model=List[schemas.RechercheResult])
def simplified_search_maisons_et_chambres(
    localisation: Optional[str] = Query(None, description="Recherche par ville/adresse de la maison (ex: Dakar)"),
    prix_min: Optional[float] = Query(None, description="Prix minimum du bien (chambre ou maison)"),
    prix_max: Optional[float] = Query(None, description="Prix maximum du bien (chambre ou maison)"),
    type_chambre: Optional[str] = Query(None, description="Type de chambre ('simple', 'appartement', 'maison') pour les recherches de chambres"),
    db: Session = Depends(get_db),
    skip: int = Query(0, description="Nombre d'éléments à sauter"),
    limit: int = Query(100, description="Nombre maximum d'éléments à retourner")
):
    results = []
    
    # Construire la requête de base pour les chambres, car toutes les recherches
    # de "biens" (maisons ou chambres) passent par les chambres disponibles.
    # Nous joignons toujours à la Maison pour l'adresse.
    query = db.query(models.Chambre).join(models.Maison)

    # Filtrer par localisation (adresse de la Maison)
    if localisation:
        query = query.filter(
            models.Maison.adresse.ilike(f"%{localisation}%")
        )

    # Filtrer par prix (sur la Chambre)
    if prix_min is not None:
        query = query.filter(models.Chambre.prix >= prix_min)
    if prix_max is not None:
        query = query.filter(models.Chambre.prix <= prix_max)

    # Filtrer par type de chambre
    if type_chambre:
        # Votre modèle Chambre a un champ 'type' qui peut être 'simple', 'appartement', 'maison'
        query = query.filter(models.Chambre.type == type_chambre)

    # Exécuter la requête et charger les relations Maison et Chambres (si applicable)
    # Nous chargeons toujours la maison associée à la chambre
    chambres = query.options(joinedload(models.Chambre.maison)).offset(skip).limit(limit).all()

    # Formater les résultats dans le schéma RechercheResult
    for chambre in chambres:
        # Utilisez l'adresse de la maison parente pour la localisation
        maison_adresse = chambre.maison.adresse if chambre.maison else "N/A"
        
        # Pour une recherche simplifiée, chaque résultat peut être une "chambre"
        # mais on peut aussi décider de renvoyer la "maison" entière si tous ses critères de chambres sont remplis.
        # Ici, on va retourner chaque chambre trouvée, avec l'adresse de sa maison.
        
        results.append(schemas.RechercheResult(
            id=chambre.id,
            type_bien="chambre", # On renvoie ici le type spécifique du bien trouvé (chambre)
            adresse=maison_adresse,
            prix=chambre.prix,
            description=chambre.description, # Description de la chambre
            details={
                "titre_chambre": chambre.titre,
                "type_chambre": chambre.type,
                "meublee": chambre.meublee,
                "salle_de_bain_privee": chambre.salle_de_bain,
                "disponible": chambre.disponible,
                "maison_id": chambre.maison_id,
                "description_maison": chambre.maison.description if chambre.maison else None,
                # Ajoutez d'autres détails pertinents de la chambre ou de sa maison
            }
        ))
    
    return results