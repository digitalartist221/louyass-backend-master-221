from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, date

from app import models, schemas
from app.database import get_db
from app.services.email_service import send_email # Assuming you have this service
from app.auth.utils import get_current_user

router = APIRouter(
    prefix="/contrats",
    tags=["Contrats"],
)

# --- Utility functions for email generation (similar to rendez-vous) ---
def generate_contrat_email_body(contrat: models.Contrat, action: str):
    locataire_nom = f"{contrat.locataire.prenom} {contrat.locataire.nom}" if contrat.locataire else "Cher locataire"
    proprietaire_nom = f"{contrat.chambre.maison.proprietaire.prenom} {contrat.chambre.maison.proprietaire.nom}" if contrat.chambre and contrat.chambre.maison and contrat.chambre.maison.proprietaire else "Le propriétaire"
    chambre_titre = contrat.chambre.titre if contrat.chambre else "une chambre"
    adresse_chambre = contrat.chambre.maison.adresse if contrat.chambre and contrat.chambre.maison else "non spécifiée"

    subject = ""
    html_content = ""

    if action == "creation":
        subject = f"Votre contrat de location pour '{chambre_titre}' est actif"
        html_content = f"""
        <html>
        <body>
            <p>Bonjour {locataire_nom},</p>
            <p>Votre contrat de location pour la chambre <strong>'{chambre_titre}'</strong> a été créé et est maintenant <strong>actif</strong>.</p>
            <p><strong>Détails du Contrat :</strong></p>
            <ul>
                <li>Date de Début: {contrat.date_debut.strftime('%d/%m/%Y')}</li>
                <li>Date de Fin: {contrat.date_fin.strftime('%d/%m/%Y')}</li>
                <li>Montant Caution: {contrat.montant_caution} CFA</li>
                <li>Périodicité Paiement: {contrat.periodicite}</li>
                <li>Adresse: {adresse_chambre}</li>
                <li>Propriétaire: {proprietaire_nom}</li>
            </ul>
            <p>Veuillez consulter votre espace personnel pour tous les détails du contrat.</p>
            <p>Cordialement,<br>L'équipe Immobilière</p>
        </body>
        </html>
        """
    elif action == "resiliation":
        subject = f"Résiliation de votre contrat de location pour '{chambre_titre}'"
        html_content = f"""
        <html>
        <body>
            <p>Bonjour {locataire_nom},</p>
            <p>Votre contrat de location pour la chambre <strong>'{chambre_titre}'</strong> a été <strong>résilié</strong>.</p>
            <p><strong>Détails du Contrat :</strong></p>
            <ul>
                <li>Date de Début: {contrat.date_debut.strftime('%d/%m/%Y')}</li>
                <li>Date de Fin Initiale: {contrat.date_fin.strftime('%d/%m/%Y')}</li>
                <li>Adresse: {adresse_chambre}</li>
            </ul>
            <p>Pour toute question ou information complémentaire, veuillez contacter le propriétaire ou notre support.</p>
            <p>Cordialement,<br>L'équipe Immobilière</p>
        </body>
        </html>
        """
    return subject, html_content

def generate_owner_contrat_notification(contrat: models.Contrat, action: str):
    proprietaire_nom = f"{contrat.chambre.maison.proprietaire.prenom} {contrat.chambre.maison.proprietaire.nom}"
    locataire_nom = f"{contrat.locataire.prenom} {contrat.locataire.nom}"
    chambre_titre = contrat.chambre.titre
    adresse_chambre = contrat.chambre.maison.adresse

    subject = ""
    html_content = ""

    if action == "creation":
        subject = f"Nouveau contrat de location actif pour '{chambre_titre}'"
        html_content = f"""
        <html>
        <body>
            <p>Bonjour {proprietaire_nom},</p>
            <p>Un nouveau contrat de location a été créé pour votre chambre :</p>
            <p><strong>'{chambre_titre}'</strong> - {adresse_chambre}</p>
            <p><strong>Locataire :</strong> {locataire_nom}</p>
            <p><strong>Date de Début :</strong> {contrat.date_debut.strftime('%d/%m/%Y')}</p>
            <p><strong>Date de Fin :</strong> {contrat.date_fin.strftime('%d/%m/%Y')}</p>
            <p><strong>Montant Caution :</strong> {contrat.montant_caution} CFA ({contrat.mois_caution} mois)</p>
            <p><strong>Périodicité de Paiement :</strong> {contrat.periodicite}</p>
            <p>Ce contrat est maintenant <strong>actif</strong>.</p>
            <p>Cordialement,<br>L'équipe Immobilière</p>
        </body>
        </html>
        """
    elif action == "resiliation":
        subject = f"Contrat résilié pour '{chambre_titre}'"
        html_content = f"""
        <html>
        <body>
            <p>Bonjour {proprietaire_nom},</p>
            <p>Le contrat de location pour votre chambre <strong>'{chambre_titre}'</strong> avec {locataire_nom} a été <strong>résilié</strong>.</p>
            <p><strong>Date de Début du Contrat :</strong> {contrat.date_debut.strftime('%d/%m/%Y')}</p>
            <p><strong>Adresse :</strong> {adresse_chambre}</p>
            <p>Cordialement,<br>L'équipe Immobilière</p>
        </body>
        </html>
        """
    return subject, html_content

# --- API Endpoints ---

@router.post("/", response_model=schemas.ContratResponse, status_code=status.HTTP_201_CREATED)
def create_contrat(
    contrat: schemas.ContratCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Only a proprietaire can create a contract
    if current_user.role != "proprietaire":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les propriétaires peuvent créer des contrats"
        )

    # Load chambre with maison and proprietaire
    db_chambre = db.query(models.Chambre).options(
        joinedload(models.Chambre.maison).joinedload(models.Maison.proprietaire)
    ).filter(models.Chambre.id == contrat.chambre_id).first()

    if not db_chambre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chambre non trouvée"
        )

    # Verify current user is the owner of the chambre
    if db_chambre.maison.proprietaire.id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas le propriétaire de cette chambre"
        )

    # Load locataire
    db_locataire = db.query(models.User).filter(models.User.id == contrat.locataire_id, models.User.role == "locataire").first()
    if not db_locataire:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Locataire non trouvé"
        )
    
    # --- Critical: Check for a confirmed rendez-vous for this locataire and chambre ---
    # We need to find if there's *any* confirmed rendez-vous between this specific locataire and chambre
    # You might want to refine this to check for a *recent* or *relevant* confirmed rendez-vous.
    # For simplicity, I'll check for any confirmed rendez-vous.
    # Ensure that `models.RendezVous` exists and has `locataire_id`, `chambre_id`, and `statut` fields.
    
    # Let's ensure we are checking for a rendez-vous that happened BEFORE or AT the contract start date
    # if you want to be strict about the flow. For now, checking any confirmed.
    confirmed_rdv = db.query(models.RendezVous).filter(
        models.RendezVous.locataire_id == contrat.locataire_id,
        models.RendezVous.chambre_id == contrat.chambre_id,
        models.RendezVous.statut == "confirmé"
    ).first()

    if not confirmed_rdv:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un contrat ne peut être créé que si le locataire a un rendez-vous confirmé avec cette chambre."
        )

    # Business logic for contract creation
    if contrat.date_debut >= contrat.date_fin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La date de début doit être antérieure à la date de fin du contrat"
        )

    if contrat.date_debut < date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La date de début du contrat ne peut pas être dans le passé"
        )
    
    if contrat.mois_caution > 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le nombre de mois de caution ne peut pas dépasser 3"
        )

    # Default status for a new contract is 'actif'
    if contrat.statut and contrat.statut != "actif":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un nouveau contrat doit avoir le statut 'actif'"
        )

    db_contrat = models.Contrat(
        locataire_id=contrat.locataire_id,
        chambre_id=contrat.chambre_id,
        date_debut=contrat.date_debut,
        date_fin=contrat.date_fin,
        montant_caution=contrat.montant_caution,
        mois_caution=contrat.mois_caution,
        description=contrat.description,
        mode_paiement=contrat.mode_paiement,
        periodicite=contrat.periodicite,
        statut="actif"
    )
    db.add(db_contrat)
    db.commit()
    db.refresh(db_contrat)

    # Load relations for emails
    db_contrat = db.query(models.Contrat).options(
        joinedload(models.Contrat.locataire),
        joinedload(models.Contrat.chambre).joinedload(models.Chambre.maison).joinedload(models.Maison.proprietaire)
    ).filter(models.Contrat.id == db_contrat.id).first()

    # Send email to locataire
    subject_locataire, html_body_locataire = generate_contrat_email_body(db_contrat, "creation")
    background_tasks.add_task(send_email, db_contrat.locataire.email, subject_locataire, html_body_locataire, html_body_locataire)

    # Send notification to proprietaire
    owner_email = db_contrat.chambre.maison.proprietaire.email
    subject_owner, html_body_owner = generate_owner_contrat_notification(db_contrat, "creation")
    background_tasks.add_task(send_email, owner_email, subject_owner, html_body_owner, html_body_owner)

    # Return response
    return schemas.ContratResponse(
        id=db_contrat.id,
        locataire_id=db_contrat.locataire_id,
        chambre_id=db_contrat.chambre_id,
        date_debut=db_contrat.date_debut,
        date_fin=db_contrat.date_fin,
        montant_caution=db_contrat.montant_caution,
        mois_caution=db_contrat.mois_caution,
        description=db_contrat.description,
        mode_paiement=db_contrat.mode_paiement,
        periodicite=db_contrat.periodicite,
        statut=db_contrat.statut,
        cree_le=db_contrat.cree_le,
        locataire=schemas.SimpleUserResponse(
            id=db_contrat.locataire.id,
            nom=f"{db_contrat.locataire.prenom} {db_contrat.locataire.nom}",
            email=db_contrat.locataire.email
        ) if db_contrat.locataire else None,
        chambre=schemas.ChambreResponse( # Assuming ChambreResponse is defined elsewhere and has nested MaisonResponse
            id=db_contrat.chambre.id,
            maison_id=db_contrat.chambre.maison_id,
            titre=db_contrat.chambre.titre,
            description=db_contrat.chambre.description,
            taille=db_contrat.chambre.taille,
            type=db_contrat.chambre.type,
            meublee=db_contrat.chambre.meublee,
            prix=db_contrat.chambre.prix,
            capacite=db_contrat.chambre.capacite,
            salle_de_bain=db_contrat.chambre.salle_de_bain,
            disponible=db_contrat.chambre.disponible,
            cree_le=db_contrat.chambre.cree_le,
            maison=schemas.MaisonResponse(
                id=db_contrat.chambre.maison.id,
                proprietaire_id=db_contrat.chambre.maison.proprietaire_id,
                nom=db_contrat.chambre.maison.nom,
                adresse=db_contrat.chambre.maison.adresse,
                ville=db_contrat.chambre.maison.ville,
                latitude=db_contrat.chambre.maison.latitude,
                superficie=db_contrat.chambre.maison.superficie,
                longitude=db_contrat.chambre.maison.longitude,
                description=db_contrat.chambre.maison.description,
                cree_le=db_contrat.chambre.maison.cree_le
            )
        ) if db_contrat.chambre else None
    )


@router.get("/", response_model=List[schemas.ContratResponse])
def read_contrats(
    statut: Optional[str] = Query(None, description="Filtre par statut du contrat"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(models.Contrat).options(
        joinedload(models.Contrat.locataire),
        joinedload(models.Contrat.chambre)
        .joinedload(models.Chambre.maison)
        .joinedload(models.Maison.proprietaire)
    )

    if current_user.role == "proprietaire":
        query = query.join(models.Chambre).join(models.Maison).filter(
            models.Maison.proprietaire_id == current_user.id
        )
    elif current_user.role == "locataire":
        query = query.filter(models.Contrat.locataire_id == current_user.id)
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Rôle utilisateur non reconnu ou non autorisé à consulter les contrats"
        )
    
    if statut:
        if statut not in ['actif', 'resilié']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Statut de filtre invalide. Doit être 'actif' ou 'resilié'."
            )
        query = query.filter(models.Contrat.statut == statut)

    contrats = query.offset(skip).limit(limit).all()

    return [
        schemas.ContratResponse(
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
                nom=f"{contrat.locataire.prenom} {contrat.locataire.nom}",
                email=contrat.locataire.email
            ) if contrat.locataire else None,
            chambre=schemas.ChambreResponse(
                id=contrat.chambre.id,
                maison_id=contrat.chambre.maison_id,
                titre=contrat.chambre.titre,
                description=contrat.chambre.description,
                taille=contrat.chambre.taille,
                type=contrat.chambre.type,
                meublee=contrat.chambre.meublee,
                prix=contrat.chambre.prix,
                capacite=contrat.chambre.capacite,
                salle_de_bain=contrat.chambre.salle_de_bain,
                disponible=contrat.chambre.disponible,
                cree_le=contrat.chambre.cree_le,
                maison=schemas.MaisonResponse(
                    id=contrat.chambre.maison.id,
                    proprietaire_id=contrat.chambre.maison.proprietaire_id,
                    nom=contrat.chambre.maison.nom,
                    adresse=contrat.chambre.maison.adresse,
                    ville=contrat.chambre.maison.ville,
                    latitude=contrat.chambre.maison.latitude,
                    superficie=contrat.chambre.maison.superficie,
                    longitude=contrat.chambre.maison.longitude,
                    description=contrat.chambre.maison.description,
                    cree_le=contrat.chambre.maison.cree_le
                )
            ) if contrat.chambre else None
        )
        for contrat in contrats
    ]


@router.get("/{contrat_id}", response_model=schemas.ContratResponse)
def read_contrat(
    contrat_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_contrat = db.query(models.Contrat).options(
        joinedload(models.Contrat.locataire),
        joinedload(models.Contrat.chambre)
        .joinedload(models.Chambre.maison)
        .joinedload(models.Maison.proprietaire)
    ).filter(models.Contrat.id == contrat_id).first()

    if not db_contrat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contrat non trouvé"
        )
    
    # Permission check for single contract retrieval
    if current_user.role == "proprietaire":
        if db_contrat.chambre.maison.proprietaire.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'êtes pas autorisé à consulter ce contrat."
            )
    elif current_user.role == "locataire":
        if db_contrat.locataire_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'êtes pas autorisé à consulter ce contrat."
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Rôle utilisateur non reconnu ou non autorisé."
        )

    return schemas.ContratResponse(
        id=db_contrat.id,
        locataire_id=db_contrat.locataire_id,
        chambre_id=db_contrat.chambre_id,
        date_debut=db_contrat.date_debut,
        date_fin=db_contrat.date_fin,
        montant_caution=db_contrat.montant_caution,
        mois_caution=db_contrat.mois_caution,
        description=db_contrat.description,
        mode_paiement=db_contrat.mode_paiement,
        periodicite=db_contrat.periodicite,
        statut=db_contrat.statut,
        cree_le=db_contrat.cree_le,
        locataire=schemas.SimpleUserResponse(
            id=db_contrat.locataire.id,
            nom=f"{db_contrat.locataire.prenom} {db_contrat.locataire.nom}",
            email=db_contrat.locataire.email
        ) if db_contrat.locataire else None,
        chambre=schemas.ChambreResponse(
            id=db_contrat.chambre.id,
            maison_id=db_contrat.chambre.maison_id,
            titre=db_contrat.chambre.titre,
            description=db_contrat.chambre.description,
            taille=db_contrat.chambre.taille,
            type=db_contrat.chambre.type,
            meublee=db_contrat.chambre.meublee,
            prix=db_contrat.chambre.prix,
            capacite=db_contrat.chambre.capacite,
            salle_de_bain=db_contrat.chambre.salle_de_bain,
            disponible=db_contrat.chambre.disponible,
            cree_le=db_contrat.chambre.cree_le,
            maison=schemas.MaisonResponse(
                id=db_contrat.chambre.maison.id,
                proprietaire_id=db_contrat.chambre.maison.proprietaire_id,
                nom=db_contrat.chambre.maison.nom,
                adresse=db_contrat.chambre.maison.adresse,
                ville=db_contrat.chambre.maison.ville,
                superficie=db_contrat.chambre.maison.superficie,
                latitude=db_contrat.chambre.maison.latitude,
                longitude=db_contrat.chambre.maison.longitude,
                description=db_contrat.chambre.maison.description,
                cree_le=db_contrat.chambre.maison.cree_le
            )
        ) if db_contrat.chambre else None
    )


@router.put("/{contrat_id}", response_model=schemas.ContratResponse)
def update_contrat(
    contrat_id: int,
    contrat_update: schemas.ContratBase, # Reusing ContratBase for update payload
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_contrat = db.query(models.Contrat).options(
        joinedload(models.Contrat.locataire),
        joinedload(models.Contrat.chambre).joinedload(models.Chambre.maison).joinedload(models.Maison.proprietaire)
    ).filter(models.Contrat.id == contrat_id).first()

    if not db_contrat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contrat non trouvé"
        )

    # Only the proprietaire of the chambre associated with the contract can update it
    if current_user.role != "proprietaire" or db_contrat.chambre.maison.proprietaire.id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas autorisé à modifier ce contrat."
        )

    # Prevent changing locataire_id or chambre_id
    if contrat_update.locataire_id != db_contrat.locataire_id or contrat_update.chambre_id != db_contrat.chambre_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Il n'est pas permis de modifier le locataire ou la chambre d'un contrat existant. Créez un nouveau contrat si nécessaire."
        )

    # Only 'resilié' status change is allowed, and only from 'actif'
    if contrat_update.statut and contrat_update.statut != db_contrat.statut:
        if contrat_update.statut == "resilié" and db_contrat.statut == "actif":
            db_contrat.statut = "resilié"
            # Send email notifications for contract termination
            subject_locataire, html_body_locataire = generate_contrat_email_body(db_contrat, "resiliation")
            background_tasks.add_task(send_email, db_contrat.locataire.email, subject_locataire, html_body_locataire, html_body_locataire)

            subject_owner, html_body_owner = generate_owner_contrat_notification(db_contrat, "resiliation")
            background_tasks.add_task(send_email, current_user.email, subject_owner, html_body_owner, html_body_owner)

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Seul le changement de statut de 'actif' à 'resilié' est permis."
            )
    
    # Update other fields, excluding statut if handled above
    update_data = contrat_update.model_dump(exclude_unset=True, exclude={'statut'})
    for key, value in update_data.items():
        setattr(db_contrat, key, value)

    # Additional validation if date_fin is updated
    if db_contrat.date_debut >= db_contrat.date_fin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La date de début doit être antérieure à la date de fin du contrat"
        )
    
    # Ensure current date is not past date_debut if updating date_debut (though not allowed in logic above)
    if db_contrat.date_debut < date.today() and db_contrat.statut == "actif":
        # This check might be redundant if date_debut cannot be changed after creation,
        # but good for safety if the logic changes.
        pass # Allow past start dates for active contracts

    db.add(db_contrat)
    db.commit()
    db.refresh(db_contrat)

    return schemas.ContratResponse(
        id=db_contrat.id,
        locataire_id=db_contrat.locataire_id,
        chambre_id=db_contrat.chambre_id,
        date_debut=db_contrat.date_debut,
        date_fin=db_contrat.date_fin,
        montant_caution=db_contrat.montant_caution,
        mois_caution=db_contrat.mois_caution,
        description=db_contrat.description,
        mode_paiement=db_contrat.mode_paiement,
        periodicite=db_contrat.periodicite,
        statut=db_contrat.statut,
        cree_le=db_contrat.cree_le,
        locataire=schemas.SimpleUserResponse(
            id=db_contrat.locataire.id,
            nom=f"{db_contrat.locataire.prenom} {db_contrat.locataire.nom}",
            email=db_contrat.locataire.email
        ) if db_contrat.locataire else None,
        chambre=schemas.ChambreResponse(
            id=db_contrat.chambre.id,
            maison_id=db_contrat.chambre.maison_id,
            titre=db_contrat.chambre.titre,
            description=db_contrat.chambre.description,
            taille=db_contrat.chambre.taille,
            type=db_contrat.chambre.type,
            meublee=db_contrat.chambre.meublee,
            prix=db_contrat.chambre.prix,
            capacite=db_contrat.chambre.capacite,
            salle_de_bain=db_contrat.chambre.salle_de_bain,
            disponible=db_contrat.chambre.disponible,
            cree_le=db_contrat.chambre.cree_le,
            maison=schemas.MaisonResponse(
                id=db_contrat.chambre.maison.id,
                proprietaire_id=db_contrat.chambre.maison.proprietaire_id,
                nom=db_contrat.chambre.maison.nom,
                adresse=db_contrat.chambre.maison.adresse,
                ville=db_contrat.chambre.maison.ville,
                superficie=db_contrat.chambre.maison.superficie,
                latitude=db_contrat.chambre.maison.latitude,
                longitude=db_contrat.chambre.maison.longitude,
                description=db_contrat.chambre.maison.description,
                cree_le=db_contrat.chambre.maison.cree_le
            )
        ) if db_contrat.chambre else None
    )


@router.delete("/{contrat_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contrat(
    contrat_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_contrat = db.query(models.Contrat).options(
        joinedload(models.Contrat.locataire),
        joinedload(models.Contrat.chambre).joinedload(models.Chambre.maison).joinedload(models.Maison.proprietaire)
    ).filter(models.Contrat.id == contrat_id).first()

    if not db_contrat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contrat non trouvé"
        )

    # Only the proprietaire can delete their contract
    if current_user.role != "proprietaire" or db_contrat.chambre.maison.proprietaire.id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas autorisé à supprimer ce contrat."
        )

    # Before deleting, send a termination notification to the tenant
    if db_contrat.statut == "actif": # Only send if not already terminated
        subject_locataire, html_body_locataire = generate_contrat_email_body(db_contrat, "resiliation")
        background_tasks.add_task(send_email, db_contrat.locataire.email, subject_locataire, html_body_locataire, html_body_locataire)
    
        # Notify owner that they deleted the contract
        subject_owner, html_body_owner = generate_owner_contrat_notification(db_contrat, "resiliation")
        background_tasks.add_task(send_email, current_user.email, subject_owner, html_body_owner, html_body_owner)

    db.delete(db_contrat)
    db.commit()