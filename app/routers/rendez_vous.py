# app/routers/rendez_vous.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
from app import models, schemas
from app.database import get_db
from app.services.email_service import send_email
from app.auth.utils import get_current_user

router = APIRouter(
    prefix="/rendez-vous",
    tags=["Rendez-vous"],
)

# --- (Your existing generate_email_body and generate_owner_notification functions) ---
def generate_email_body(rdv: models.RendezVous, statut: str):
    locataire_nom = f"{rdv.locataire.prenom} {rdv.locataire.nom}" if rdv.locataire else "Cher locataire"
    proprietaire_nom = f"{rdv.chambre.maison.proprietaire.prenom} {rdv.chambre.maison.proprietaire.nom}" if rdv.chambre and rdv.chambre.maison and rdv.chambre.maison.proprietaire else "Le propriétaire"
    chambre_titre = rdv.chambre.titre if rdv.chambre else "une chambre"
    adresse_chambre = rdv.chambre.maison.adresse if rdv.chambre and rdv.chambre.maison else "non spécifiée"

    if statut == "confirmé":
        subject = f"Rendez-vous confirmé: {chambre_titre} - {rdv.date_heure.strftime('%d/%m/%Y à %H:%M')}"
        html_content = f"""
        <html>
        <body>
            <p>Bonjour {locataire_nom},</p>
            <p>Votre rendez-vous pour la chambre <strong>'{chambre_titre}'</strong> a été confirmé.</p>
            <p><strong>Détails :</strong></p>
            <ul>
                <li>Date: {rdv.date_heure.strftime('%d/%m/%Y à %H:%M')}</li>
                <li>Adresse: {adresse_chambre}</li>
                <li>Propriétaire: {proprietaire_nom}</li>
            </ul>
            <p>Présentez-vous à l'adresse indiquée à l'heure convenue.</p>
            <p>Cordialement,<br>L'équipe Immobilière</p>
        </body>
        </html>
        """
    elif statut == "annulé":
        subject = f"Rendez-vous annulé: {chambre_titre}"
        html_content = f"""
        <html>
        <body>
            <p>Bonjour {locataire_nom},</p>
            <p>Votre rendez-vous prévu pour le {rdv.date_heure.strftime('%d/%m/%Y à %H:%M')} a été annulé.</p>
            <p><strong>Chambre :</strong> {chambre_titre}</p>
            <p><strong>Adresse :</strong> {adresse_chambre}</p>
            <p>Veuillez nous excuser pour tout inconvénient.</p>
            <p>Cordialement,<br>L'équipe Immobilière</p>
        </body>
        </html>
        """
    elif statut == "en_attente":
        subject = f"Demande de rendez-vous pour: {chambre_titre}"
        html_content = f"""
        <html>
        <body>
            <p>Bonjour {locataire_nom},</p>
            <p>Votre demande de rendez-vous pour la chambre <strong>'{chambre_titre}'</strong> a été enregistrée.</p>
            <p><strong>Date proposée :</strong> {rdv.date_heure.strftime('%d/%m/%Y à %H:%M')}</p>
            <p>Le propriétaire sera informé et vous recevrez une confirmation sous peu.</p>
            <p>Cordialement,<br>L'équipe Immobilière</p>
        </body>
        </html>
        """
    else:
        subject = f"Mise à jour de votre rendez-vous pour: {chambre_titre}"
        html_content = f"""
        <html>
        <body>
            <p>Bonjour {locataire_nom},</p>
            <p>Le statut de votre rendez-vous pour la chambre '{chambre_titre}' a été mis à jour.</p>
            <p>Nouveau statut : <strong>{statut}</strong></p>
            <p>Cordialement,<br>L'équipe Immobilière</p>
        </body>
        </html>
        """
    
    return subject, html_content

def generate_owner_notification(rdv: models.RendezVous, action: str):
    proprietaire_nom = f"{rdv.chambre.maison.proprietaire.prenom} {rdv.chambre.maison.proprietaire.nom}"
    locataire_nom = f"{rdv.locataire.prenom} {rdv.locataire.nom}"
    chambre_titre = rdv.chambre.titre
    adresse_chambre = rdv.chambre.maison.adresse

    if action == "creation":
        subject = f"Nouvelle demande de rendez-vous: {chambre_titre}"
        html_content = f"""
        <html>
        <body>
            <p>Bonjour {proprietaire_nom},</p>
            <p>Vous avez une nouvelle demande de rendez-vous pour votre chambre :</p>
            <p><strong>{chambre_titre}</strong> - {adresse_chambre}</p>
            <p><strong>Locataire :</strong> {locataire_nom}</p>
            <p><strong>Date proposée :</strong> {rdv.date_heure.strftime('%d/%m/%Y à %H:%M')}</p>
            <p><strong>Contact :</strong> {rdv.locataire.telephone or 'Non renseigné'}</p>
            <p>Veuillez confirmer ou annuler ce rendez-vous dans votre espace propriétaire.</p>
            <p>Cordialement,<br>L'équipe Immobilière</p>
        </body>
        </html>
        """
    elif action == "modification_date":
        subject = f"Modification de rendez-vous: {chambre_titre}"
        html_content = f"""
        <html>
        <body>
            <p>Bonjour {proprietaire_nom},</p>
            <p>Le locataire a modifié la date du rendez-vous pour votre chambre :</p>
            <p><strong>{chambre_titre}</strong> - {adresse_chambre}</p>
            <p><strong>Nouvelle date proposée :</strong> {rdv.date_heure.strftime('%d/%m/%Y à %H:%M')}</p>
            <p>Veuillez confirmer ou annuler ce nouveau créneau.</p>
            <p>Cordialement,<br>L'équipe Immobilière</p>
        </body>
        </html>
        """
    elif action == "annulation_locataire":
        subject = f"Annulation de rendez-vous: {chambre_titre}"
        html_content = f"""
        <html>
        <body>
            <p>Bonjour {proprietaire_nom},</p>
            <p>Le locataire a annulé le rendez-vous pour votre chambre :</p>
            <p><strong>{chambre_titre}</strong> - {adresse_chambre}</p>
            <p><strong>Date prévue :</strong> {rdv.date_heure.strftime('%d/%m/%Y à %H:%M')}</p>
            <p>Cordialement,<br>L'équipe Immobilière</p>
        </body>
        </html>
        """
    else:  # annulation_proprietaire
        subject = f"Rendez-vous annulé: {chambre_titre}"
        html_content = f"""
        <html>
        <body>
            <p>Bonjour {proprietaire_nom},</p>
            <p>Vous avez annulé le rendez-vous pour votre chambre :</p>
            <p><strong>{chambre_titre}</strong> - {adresse_chambre}</p>
            <p><strong>Date prévue :</strong> {rdv.date_heure.strftime('%d/%m/%Y à %H:%M')}</p>
            <p>Le locataire a été notifié de cette annulation.</p>
            <p>Cordialement,<br>L'équipe Immobilière</p>
        </body>
        </html>
        """
    
    return subject, html_content

# --- (Your existing create_rendez_vous route) ---
@router.post("/", response_model=schemas.RendezVousResponse, status_code=status.HTTP_201_CREATED)
def create_rendez_vous(
    rdv: schemas.RendezVousCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Vérifier que l'utilisateur est un locataire
    if current_user.role != "locataire":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les locataires peuvent créer des rendez-vous"
        )
    
    # Le locataire ne peut créer que ses propres rendez-vous
    if rdv.locataire_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous ne pouvez créer que vos propres rendez-vous"
        )

    # Charger la chambre avec la relation maison et propriétaire
    db_chambre = db.query(models.Chambre).options(
        joinedload(models.Chambre.maison).joinedload(models.Maison.proprietaire)
    ).filter(models.Chambre.id == rdv.chambre_id).first()
    
    if not db_chambre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chambre non trouvée"
        )
    
    # Vérifier que le locataire n'est pas le propriétaire
    if db_chambre.maison.proprietaire.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous ne pouvez pas créer de rendez-vous pour votre propre chambre"
        )

    # Un nouveau rendez-vous doit avoir le statut 'en_attente'
    if rdv.statut and rdv.statut != "en_attente":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un nouveau rendez-vous doit avoir le statut 'en_attente'"
        )

    # Vérifier la date
    if rdv.date_heure < datetime.now(rdv.date_heure.tzinfo):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La date du rendez-vous doit être dans le futur"
        )

    # Créer le rendez-vous
    db_rdv = models.RendezVous(
        locataire_id=current_user.id,
        chambre_id=rdv.chambre_id,
        date_heure=rdv.date_heure,
        statut="en_attente"
    )
    db.add(db_rdv)
    db.commit()
    
    # Recharger les relations pour les emails
    db_rdv = db.query(models.RendezVous).options(
        joinedload(models.RendezVous.locataire),
        joinedload(models.RendezVous.chambre).joinedload(models.Chambre.maison).joinedload(models.Maison.proprietaire)
    ).filter(models.RendezVous.id == db_rdv.id).first()

    # Envoyer email au locataire
    subject, html_body = generate_email_body(db_rdv, "en_attente")
    background_tasks.add_task(send_email, current_user.email, subject, html_body, html_body)

    # Envoyer notification au propriétaire
    owner_email = db_rdv.chambre.maison.proprietaire.email
    owner_subject, owner_html = generate_owner_notification(db_rdv, "creation")
    background_tasks.add_task(send_email, owner_email, owner_subject, owner_html, owner_html)

    # Assurez-vous que la réponse contient toutes les relations nécessaires
    return schemas.RendezVousResponse(
        id=db_rdv.id,
        locataire_id=db_rdv.locataire_id,
        chambre_id=db_rdv.chambre_id,
        date_heure=db_rdv.date_heure,
        statut=db_rdv.statut,
        cree_le=db_rdv.cree_le,
        locataire=schemas.SimpleUserResponse(
            id=db_rdv.locataire.id,
            nom=f"{db_rdv.locataire.prenom} {db_rdv.locataire.nom}",
            email=db_rdv.locataire.email
        ) if db_rdv.locataire else None,
        chambre=schemas.ChambreResponse(
            id=db_rdv.chambre.id,
            maison_id=db_rdv.chambre.maison_id,
            titre=db_rdv.chambre.titre,
            description=db_rdv.chambre.description,
            taille=db_rdv.chambre.taille,
            type=db_rdv.chambre.type,
            meublee=db_rdv.chambre.meublee,
            prix=db_rdv.chambre.prix,
            capacite=db_rdv.chambre.capacite,
            salle_de_bain=db_rdv.chambre.salle_de_bain,
            disponible=db_rdv.chambre.disponible,
            cree_le=db_rdv.chambre.cree_le,
            maison=schemas.MaisonResponse(
                id=db_rdv.chambre.maison.id,
                proprietaire_id=db_rdv.chambre.maison.proprietaire_id,
                nom=db_rdv.chambre.maison.nom,
                adresse=db_rdv.chambre.maison.adresse,
                ville=db_rdv.chambre.maison.ville,
                superficie=db_rdv.chambre.maison.superficie,
                latitude=db_rdv.chambre.maison.latitude,
                longitude=db_rdv.chambre.maison.longitude,
                description=db_rdv.chambre.maison.description,
                cree_le=db_rdv.chambre.maison.cree_le
            )
        ) if db_rdv.chambre else None
    )

@router.get("/", response_model=List[schemas.RendezVousResponse])
def read_rendez_vous(
    statut: Optional[str] = Query(None, description="Filtre par statut"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Construire la requête de base avec les relations
    query = db.query(models.RendezVous).options(
        joinedload(models.RendezVous.locataire),
        joinedload(models.RendezVous.chambre)
        .joinedload(models.Chambre.maison)
        .joinedload(models.Maison.proprietaire)
    )

    # Appliquer les filtres selon le rôle
    if current_user.role == "proprietaire":
        # Propriétaire : voir les RDV de ses chambres
        query = query.join(models.Chambre).join(models.Maison).filter(
            models.Maison.proprietaire_id == current_user.id
        )
    elif current_user.role == "locataire":
        # Locataire : voir ses propres RDV
        query = query.filter(models.RendezVous.locataire_id == current_user.id)
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Rôle utilisateur non reconnu"
        )

    # Filtrer par statut si fourni
    if statut:
        if statut not in ['en_attente', 'confirmé', 'annulé']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Statut de filtre invalide"
            )
        query = query.filter(models.RendezVous.statut == statut)

    # Exécuter la requête
    rdvs = query.offset(skip).limit(limit).all()
    
    # Construire les réponses avec le bon schéma
    return [
        schemas.RendezVousResponse(
            id=rdv.id,
            locataire_id=rdv.locataire_id,
            chambre_id=rdv.chambre_id,
            date_heure=rdv.date_heure,
            statut=rdv.statut,
            cree_le=rdv.cree_le,
            locataire=schemas.SimpleUserResponse(
                id=rdv.locataire.id,
                nom=f"{rdv.locataire.prenom} {rdv.locataire.nom}",
                email=rdv.locataire.email
            ) if rdv.locataire else None,
            chambre=schemas.ChambreResponse(
                id=rdv.chambre.id,
                maison_id=rdv.chambre.maison_id,
                titre=rdv.chambre.titre,
                description=rdv.chambre.description,
                taille=rdv.chambre.taille,
                type=rdv.chambre.type,
                meublee=rdv.chambre.meublee,
                prix=rdv.chambre.prix,
                capacite=rdv.chambre.capacite,
                salle_de_bain=rdv.chambre.salle_de_bain,
                disponible=rdv.chambre.disponible,
                cree_le=rdv.chambre.cree_le,
                maison=schemas.MaisonResponse(
                    id=rdv.chambre.maison.id,
                    proprietaire_id=rdv.chambre.maison.proprietaire_id,
                    nom=rdv.chambre.maison.nom,
                    adresse=rdv.chambre.maison.adresse,
                    ville=rdv.chambre.maison.ville,
                    superficie=rdv.chambre.maison.superficie,
                    latitude=rdv.chambre.maison.latitude,
                    longitude=rdv.chambre.maison.longitude,
                    description=rdv.chambre.maison.description,
                    cree_le=rdv.chambre.maison.cree_le
                )
            ) if rdv.chambre else None
        )
        for rdv in rdvs
    ]

# --- (Your existing update_rendez_vous and delete_rendez_vous routes) ---

@router.put("/{rdv_id}", response_model=schemas.RendezVousResponse)
def update_rendez_vous(
    rdv_id: int,
    rdv_update: schemas.RendezVousUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Charger le rendez-vous avec toutes les relations nécessaires
    db_rdv = db.query(models.RendezVous).options(
        joinedload(models.RendezVous.locataire),
        joinedload(models.RendezVous.chambre).joinedload(models.Chambre.maison).joinedload(models.Maison.proprietaire)
    ).filter(models.RendezVous.id == rdv_id).first()

    if not db_rdv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rendez-vous non trouvé"
        )

    # VÉRIFICATION DES PERMISSIONS
    is_owner = False
    is_tenant = False
    
    if current_user.role == "proprietaire":
        is_owner = db_rdv.chambre.maison.proprietaire.id == current_user.id
        if not is_owner:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'êtes pas le propriétaire de cette chambre"
            )
            
    elif current_user.role == "locataire":
        is_tenant = db_rdv.locataire_id == current_user.id
        if not is_tenant:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'êtes pas le locataire de ce rendez-vous"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Action non autorisée"
        )

    # LOGIQUE DE MISE À JOUR
    # Propriétaire : peut confirmer ou annuler
    if is_owner:
        if rdv_update.date_heure:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Seul le locataire peut modifier la date"
            )
            
        if not rdv_update.statut or rdv_update.statut not in ["confirmé", "annulé"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Action invalide pour un propriétaire"
            )
            
        # Confirmation
        if rdv_update.statut == "confirmé":
            if db_rdv.statut != "en_attente":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Seuls les rendez-vous en attente peuvent être confirmés"
                )
            db_rdv.statut = "confirmé"
            # Envoyer email au locataire
            subject, html_body = generate_email_body(db_rdv, "confirmé")
            background_tasks.add_task(send_email, db_rdv.locataire.email, subject, html_body, html_body)
            
        # Annulation
        elif rdv_update.statut == "annulé":
            db_rdv.statut = "annulé"
            # Envoyer email au locataire
            subject, html_body = generate_email_body(db_rdv, "annulé")
            background_tasks.add_task(send_email, db_rdv.locataire.email, subject, html_body, html_body)
            # Notification au propriétaire
            owner_subject, owner_html = generate_owner_notification(db_rdv, "annulation_proprietaire")
            background_tasks.add_task(send_email, current_user.email, owner_subject, owner_html, owner_html)
    
    # Locataire : peut modifier la date
    elif is_tenant:
        if rdv_update.statut and rdv_update.statut != "en_attente":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous ne pouvez que modifier la date du rendez-vous"
            )
            
        if not rdv_update.date_heure:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nouvelle date requise"
            )
            
        # Vérifier la nouvelle date
        if rdv_update.date_heure < datetime.now(rdv_update.date_heure.tzinfo):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La nouvelle date doit être dans le futur"
            )
            
        db_rdv.date_heure = rdv_update.date_heure
        db_rdv.statut = "en_attente"  # Retour en attente de confirmation
        
        # Envoyer notification au propriétaire
        owner_email = db_rdv.chambre.maison.proprietaire.email
        owner_subject, owner_html = generate_owner_notification(db_rdv, "modification_date")
        background_tasks.add_task(send_email, owner_email, owner_subject, owner_html, owner_html)

    # Sauvegarder les modifications
    db.add(db_rdv)
    db.commit()
    db.refresh(db_rdv)
    
    # Construire la réponse avec le bon schéma
    return schemas.RendezVousResponse(
        id=db_rdv.id,
        locataire_id=db_rdv.locataire_id,
        chambre_id=db_rdv.chambre_id,
        date_heure=db_rdv.date_heure,
        statut=db_rdv.statut,
        cree_le=db_rdv.cree_le,
        locataire=schemas.SimpleUserResponse(
            id=db_rdv.locataire.id,
            nom=f"{db_rdv.locataire.prenom} {db_rdv.locataire.nom}",
            email=db_rdv.locataire.email
        ) if db_rdv.locataire else None,
        chambre=schemas.ChambreResponse(
            id=db_rdv.chambre.id,
            maison_id=db_rdv.chambre.maison_id,
            titre=db_rdv.chambre.titre,
            description=db_rdv.chambre.description,
            taille=db_rdv.chambre.taille,
            type=db_rdv.chambre.type,
            meublee=db_rdv.chambre.meublee,
            prix=db_rdv.chambre.prix,
            capacite=db_rdv.chambre.capacite,
            salle_de_bain=db_rdv.chambre.salle_de_bain,
            disponible=db_rdv.chambre.disponible,
            cree_le=db_rdv.chambre.cree_le,
            maison=schemas.MaisonResponse(
                id=db_rdv.chambre.maison.id,
                proprietaire_id=db_rdv.chambre.maison.proprietaire_id,
                nom=db_rdv.chambre.maison.nom,
                adresse=db_rdv.chambre.maison.adresse,
                ville=db_rdv.chambre.maison.ville,
                superficie=db_rdv.chambre.maison.superficie,
                latitude=db_rdv.chambre.maison.latitude,
                longitude=db_rdv.chambre.maison.longitude,
                description=db_rdv.chambre.maison.description,
                cree_le=db_rdv.chambre.maison.cree_le
            )
        ) if db_rdv.chambre else None
    )

@router.delete("/{rdv_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rendez_vous(
    rdv_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Charger le rendez-vous avec les relations
    db_rdv = db.query(models.RendezVous).options(
        joinedload(models.RendezVous.locataire),
        joinedload(models.RendezVous.chambre).joinedload(models.Chambre.maison).joinedload(models.Maison.proprietaire)
    ).filter(models.RendezVous.id == rdv_id).first()
    
    if not db_rdv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rendez-vous non trouvé"
        )

    # VÉRIFICATION DES PERMISSIONS
    is_owner = False
    is_tenant = False
    
    if current_user.role == "proprietaire":
        is_owner = db_rdv.chambre.maison.proprietaire.id == current_user.id
        if not is_owner:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'êtes pas le propriétaire de cette chambre"
            )
            
    elif current_user.role == "locataire":
        is_tenant = db_rdv.locataire_id == current_user.id
        if not is_tenant:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'êtes pas le locataire de ce rendez-vous"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Action non autorisée"
        )

    # PRÉPARER LES NOTIFICATIONS
    if is_owner:
        # Propriétaire supprime → notifier locataire
        recipient = db_rdv.locataire.email
        subject, html_content = generate_email_body(db_rdv, "annulé")
        # Notification au propriétaire
        owner_subject, owner_html = generate_owner_notification(db_rdv, "annulation_proprietaire")
        background_tasks.add_task(send_email, current_user.email, owner_subject, owner_html, owner_html)
        
    elif is_tenant:
        # Locataire supprime → notifier propriétaire
        recipient = db_rdv.chambre.maison.proprietaire.email
        subject, html_content = generate_owner_notification(db_rdv, "annulation_locataire")
    
    # Envoyer la notification
    background_tasks.add_task(send_email, recipient, subject, html_content, html_content)

    # Supprimer le rendez-vous
    db.delete(db_rdv)
    db.commit()
    return