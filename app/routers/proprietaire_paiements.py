# app/api/endpoints/proprietaire_paiements.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, date, timedelta

from app import models, schemas
from app.database import get_db
from app.auth.utils import get_current_user
from app.routers.locataire_contrats import build_contrat_response # Réutiliser la fonction existante

router = APIRouter(
    prefix="/proprietaire/paiements",
    tags=["Proprietaire Paiements"]
)

@router.get(
    "/",
    response_model=List[schemas.PaiementDetailResponse],
    summary="Récupérer tous les paiements pour les maisons du propriétaire connecté"
)
async def get_my_properties_payments(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role != "proprietaire":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les propriétaires peuvent voir les paiements de leurs maisons."
        )

    # Récupérer les paiements associés aux contrats des chambres appartenant aux maisons du propriétaire
    paiements = db.query(models.Paiement).options(
        joinedload(models.Paiement.contrat)
        .joinedload(models.Contrat.locataire),
        joinedload(models.Paiement.contrat)
        .joinedload(models.Contrat.chambre)
        .joinedload(models.Chambre.maison)
    ).join(
        models.Contrat
    ).join(
        models.Chambre
    ).join(
        models.Maison
    ).filter(
        models.Maison.proprietaire_id == current_user.id
    ).all()

    return [
        schemas.PaiementDetailResponse(
            id=p.id,
            contrat_id=p.contrat_id,
            montant=p.montant,
            statut=p.statut,
            date_echeance=p.date_echeance,
            date_paiement=p.date_paiement,
            cree_le=p.cree_le,
            contrat=schemas.ContratResponse.from_orm(p.contrat),
            chambre=schemas.ChambreResponse(
                id=p.contrat.chambre.id,
                cree_le=p.contrat.chambre.cree_le,
                maison_id=p.contrat.chambre.maison_id,
                titre=p.contrat.chambre.titre,
                description=p.contrat.chambre.description,
                taille=p.contrat.chambre.taille,
                type=p.contrat.chambre.type,
                meublee=p.contrat.chambre.meublee,
                prix=p.contrat.chambre.prix,
                capacite=p.contrat.chambre.capacite,
                salle_de_bain=p.contrat.chambre.salle_de_bain,
                disponible=p.contrat.chambre.disponible,
                maison=schemas.MaisonResponse.from_orm(p.contrat.chambre.maison)
            ),
            locataire=schemas.SimpleUserResponse.from_orm(p.contrat.locataire)
        ) for p in paiements
    ]

@router.get(
    "/pending-this-month",
    response_model=List[schemas.PaiementDetailResponse],
    summary="Récupérer les paiements en attente pour le mois en cours pour les maisons du propriétaire"
)
async def get_pending_payments_this_month(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role != "proprietaire":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les propriétaires peuvent voir les paiements en attente."
        )

    today = date.today()
    first_day_of_month = today.replace(day=1)
    last_day_of_month = today.replace(day=1, month=today.month % 12 + 1, year=today.year + (1 if today.month == 12 else 0)) - timedelta(days=1)


    # Récupérer les paiements en attente pour le mois en cours pour les maisons du propriétaire
    paiements_en_attente = db.query(models.Paiement).options(
        joinedload(models.Paiement.contrat)
        .joinedload(models.Contrat.locataire),
        joinedload(models.Paiement.contrat)
        .joinedload(models.Contrat.chambre)
        .joinedload(models.Chambre.maison)
    ).join(
        models.Contrat
    ).join(
        models.Chambre
    ).join(
        models.Maison
    ).filter(
        models.Maison.proprietaire_id == current_user.id,
        models.Paiement.statut == 'en_attente',
        models.Paiement.date_echeance >= first_day_of_month,
        models.Paiement.date_echeance <= last_day_of_month
    ).all()

    return [
        schemas.PaiementDetailResponse(
            id=p.id,
            contrat_id=p.contrat_id,
            montant=p.montant,
            statut=p.statut,
            date_echeance=p.date_echeance,
            date_paiement=p.date_paiement,
            cree_le=p.cree_le,
            contrat=schemas.ContratResponse.from_orm(p.contrat),
            chambre=schemas.ChambreResponse(
                id=p.contrat.chambre.id,
                cree_le=p.contrat.chambre.cree_le,
                maison_id=p.contrat.chambre.maison_id,
                titre=p.contrat.chambre.titre,
                description=p.contrat.chambre.description,
                taille=p.contrat.chambre.taille,
                type=p.contrat.chambre.type,
                meublee=p.contrat.chambre.meublee,
                prix=p.contrat.chambre.prix,
                capacite=p.contrat.chambre.capacite,
                salle_de_bain=p.contrat.chambre.salle_de_bain,
                disponible=p.contrat.chambre.disponible,
                maison=schemas.MaisonResponse.from_orm(p.contrat.chambre.maison)
            ),
            locataire=schemas.SimpleUserResponse.from_orm(p.contrat.locataire)
        ) for p in paiements_en_attente
    ]