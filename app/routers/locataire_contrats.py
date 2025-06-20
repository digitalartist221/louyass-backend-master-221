# app/api/endpoints/locataire_contrats.py
from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app import models, schemas
from app.database import get_db
from app.auth.utils import get_current_user

router = APIRouter(
    prefix="/locataire/contrats",
    tags=["Locataire Contrats"]
)

def build_contrat_response(contrat: models.Contrat) -> Dict:
    """Construit la réponse Contrat sous forme de dictionnaire avec les objets imbriqués."""
    response = {
        "id": contrat.id,
        "locataire_id": contrat.locataire_id,
        "chambre_id": contrat.chambre_id,
        "date_debut": contrat.date_debut,
        "date_fin": contrat.date_fin,
        "montant_caution": contrat.montant_caution,
        "mois_caution": contrat.mois_caution,
        "description": contrat.description,
        "mode_paiement": contrat.mode_paiement,
        "periodicite": contrat.periodicite,
        "statut": contrat.statut,
        "cree_le": contrat.cree_le,
        "locataire": None,
        "chambre": None
    }

    if contrat.locataire:
        response["locataire"] = {
            "id": contrat.locataire.id,
            "nom": contrat.locataire.nom,
            "prenom": contrat.locataire.prenom,
            "email": contrat.locataire.email
        }

    if contrat.chambre:
        response["chambre"] = {
            "id": contrat.chambre.id,
            "maison_id": contrat.chambre.maison_id,
            "titre": contrat.chambre.titre,
            "description": contrat.chambre.description,
            "taille": contrat.chambre.taille,
            "type": contrat.chambre.type,
            "meublee": contrat.chambre.meublee,
            "prix": contrat.chambre.prix,
            "capacite": contrat.chambre.capacite,
            "salle_de_bain": contrat.chambre.salle_de_bain,
            "disponible": contrat.chambre.disponible,
            "maison": None
        }
        if contrat.chambre.maison:
            response["chambre"]["maison"] = {
                "id": contrat.chambre.maison.id,
                "adresse": contrat.chambre.maison.adresse,
                "ville": contrat.chambre.maison.ville,
                "superficie": contrat.chambre.maison.superficie,
                "latitude": contrat.chambre.maison.latitude,
                "longitude": contrat.chambre.maison.longitude,
                "description": contrat.chambre.maison.description,
                "proprietaire_id": contrat.chambre.maison.proprietaire_id,
                "cree_le": contrat.chambre.maison.cree_le
            }
    return response

@router.get(
    "/",
    summary="Récupérer tous les contrats pour le locataire connecté"
)
async def read_my_contrats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role != "locataire":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les locataires peuvent voir leurs contrats."
        )

    # Chargement des contrats avec les relations nécessaires
    contrats = db.query(models.Contrat).options(
        joinedload(models.Contrat.locataire),
        joinedload(models.Contrat.chambre).joinedload(models.Chambre.maison)
    ).filter(models.Contrat.locataire_id == current_user.id).all()

    return [build_contrat_response(c) for c in contrats]

@router.get(
    "/{contrat_id}/paiements",
    summary="Récupérer tous les paiements pour un contrat spécifique du locataire"
)
async def get_contract_payments(
    contrat_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Vérifier que le contrat appartient au locataire
    contrat = db.query(models.Contrat).options(
        joinedload(models.Contrat.locataire),
        joinedload(models.Contrat.chambre).joinedload(models.Chambre.maison)
    ).filter(models.Contrat.id == contrat_id).first()

    if not contrat or contrat.locataire_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contrat non trouvé ou accès non autorisé"
        )

    # Récupérer les paiements du contrat
    paiements = db.query(models.Paiement).filter(
        models.Paiement.contrat_id == contrat_id
    ).all()

    # Construire les réponses de paiement
    response_data = []
    for p in paiements:
        response_data.append({
            "id": p.id,
            "contrat_id": p.contrat_id,
            "montant": p.montant,
            "statut": p.statut,
            "date_echeance": p.date_echeance,
            "date_paiement": p.date_paiement,
            "cree_le": p.cree_le,
            "contrat": build_contrat_response(contrat)
        })
    return response_data