# app/api/endpoints/paiements.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, date

from app import models, schemas
from app.database import get_db
from app.auth.utils import get_current_user
from app.services.email_service import send_email

router = APIRouter(
    prefix="/paiements",
    tags=["Paiements"]
)

# Helper pour construire la réponse Contrat selon le schéma
def build_contrat_response(contrat: models.Contrat) -> schemas.ContratResponse:
    return schemas.ContratResponse(
        id=contrat.id,
        locataire_id=contrat.locataire_id,
        chambre_id=contrat.chambre_id,
        date_debut=contrat.date_debut,
        date_fin=contrat.date_fin,
        montant_caution=contrat.montant_caution,
        mois_caution=contrat.mois_caution,
        description=contrat.description,
        mode_paiement=contrat.mode_paiement,
        periodicite=contrat.periodicite,
        statut=contrat.statut,
        cree_le=contrat.cree_le,
        locataire=schemas.SimpleUserResponse(
            id=contrat.locataire.id,
            nom=contrat.locataire.nom,
            prenom=contrat.locataire.prenom,
            email=contrat.locataire.email
        ) if contrat.locataire else None,
        chambre=schemas.ChambreBase(
            maison_id=contrat.chambre.maison_id,
            titre=contrat.chambre.titre,
            description=contrat.chambre.description,
            taille=contrat.chambre.taille,
            type=contrat.chambre.type,
            meublee=contrat.chambre.meublee,
            prix=contrat.chambre.prix,
            capacite=contrat.chambre.capacite,
            salle_de_bain=contrat.chambre.salle_de_bain,
            disponible=contrat.chambre.disponible
        ) if contrat.chambre else None
    )

@router.post(
    "/",
    response_model=schemas.PaiementResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_paiement(
    paiement_in: schemas.PaiementCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Vérifier que le contrat existe
    contrat = db.query(models.Contrat).options(
        joinedload(models.Contrat.locataire),
        joinedload(models.Contrat.chambre).joinedload(models.Chambre.maison)
    ).filter(models.Contrat.id == paiement_in.contrat_id).first()
    
    if not contrat:
        raise HTTPException(status_code=404, detail="Contrat non trouvé")

    # Vérification des permissions
    if current_user.role == "locataire":
        if contrat.locataire_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Action non autorisée pour ce locataire"
            )
        # Validation supplémentaire pour les locataires
        if paiement_in.statut != 'paye' or not paiement_in.date_paiement:
            raise HTTPException(
                status_code=400,
                detail="Les locataires doivent marquer le paiement comme 'paye' avec date"
            )
    
    elif current_user.role == "proprietaire":
        if not contrat.chambre or not contrat.chambre.maison or contrat.chambre.maison.proprietaire_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Action non autorisée pour ce propriétaire"
            )
    
    # Création du paiement
    db_paiement = models.Paiement(**paiement_in.dict())
    db.add(db_paiement)
    db.commit()
    db.refresh(db_paiement)

    # Envoi de notification
    if db_paiement.statut == 'paye' and contrat.chambre and contrat.chambre.maison:
        send_email(
            to_email=contrat.chambre.maison.proprietaire.email,
            subject="Nouveau paiement reçu",
            body=f"Paiement de {db_paiement.montant} CFA reçu pour le contrat {contrat.id}"
        )

    return schemas.PaiementResponse(
        id=db_paiement.id,
        contrat_id=db_paiement.contrat_id,
        montant=db_paiement.montant,
        statut=db_paiement.statut,
        date_echeance=db_paiement.date_echeance,
        date_paiement=db_paiement.date_paiement,
        cree_le=db_paiement.cree_le,
        contrat=build_contrat_response(contrat)
    )

@router.get(
    "/{paiement_id}",
    response_model=schemas.PaiementResponse
)
async def read_paiement(
    paiement_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    paiement = db.query(models.Paiement).get(paiement_id)
    if not paiement:
        raise HTTPException(status_code=404, detail="Paiement non trouvé")

    # Charger les relations nécessaires
    contrat = db.query(models.Contrat).options(
        joinedload(models.Contrat.locataire),
        joinedload(models.Contrat.chambre).joinedload(models.Chambre.maison)
    ).filter(models.Contrat.id == paiement.contrat_id).first()

    if not contrat:
        raise HTTPException(status_code=404, detail="Contrat associé introuvable")

    # Vérification des permissions
    if current_user.role == "locataire" and contrat.locataire_id != current_user.id:
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    if current_user.role == "proprietaire":
        if not contrat.chambre or not contrat.chambre.maison or contrat.chambre.maison.proprietaire_id != current_user.id:
            raise HTTPException(status_code=403, detail="Accès non autorisé")

    return schemas.PaiementResponse(
        id=paiement.id,
        contrat_id=paiement.contrat_id,
        montant=paiement.montant,
        statut=paiement.statut,
        date_echeance=paiement.date_echeance,
        date_paiement=paiement.date_paiement,
        cree_le=paiement.cree_le,
        contrat=build_contrat_response(contrat)
    )

@router.get(
    "/me",
    response_model=List[schemas.PaiementResponse]
)
async def get_my_payments(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(models.Paiement).options(
        joinedload(models.Paiement.contrat).joinedload(models.Contrat.locataire),
        joinedload(models.Paiement.contrat).joinedload(models.Contrat.chambre).joinedload(models.Chambre.maison)
    )

    if current_user.role == "locataire":
        paiements = query.join(models.Contrat).filter(models.Contrat.locataire_id == current_user.id).all()
    elif current_user.role == "proprietaire":
        paiements = query.join(models.Contrat).join(models.Chambre).filter(models.Chambre.maison.has(proprietaire_id=current_user.id)).all()
    else:
        paiements = query.all()

    return [
        schemas.PaiementResponse(
            id=p.id,
            contrat_id=p.contrat_id,
            montant=p.montant,
            statut=p.statut,
            date_echeance=p.date_echeance,
            date_paiement=p.date_paiement,
            cree_le=p.cree_le,
            contrat=build_contrat_response(p.contrat)
        ) for p in paiements
    ]

# Les autres endpoints (update, mark_as_paid) suivent le même pattern