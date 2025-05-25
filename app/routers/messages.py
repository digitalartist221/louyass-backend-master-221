# app/routers/messages.py

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload # Pour charger les relations
from datetime import datetime

from app import models, schemas
from app.database import get_db
# Assurez-vous d'avoir une dépendance pour récupérer l'utilisateur actuel (authentifié)
# Si vous utilisez OAuth2, ce sera quelque chose comme `get_current_user` ou `get_current_active_user`
from app.auth.routes import get_current_active_user # Adaptez ceci à votre fonction d'authentification

router = APIRouter(
    prefix="/messages",
    tags=["Messages"],
)

@router.post("/", response_model=schemas.MessageResponse, status_code=status.HTTP_201_CREATED)
def send_message(
    message: schemas.MessageBase, # Utilise MessageBase car l'expéditeur est issu du token
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Permet à un utilisateur (bailleur ou locataire) d'envoyer un message à un autre utilisateur.
    L'expéditeur est automatiquement défini comme l'utilisateur authentifié.
    """
    # Vérifier que le destinataire existe
    db_destinataire = db.query(models.User).filter(models.User.id == message.destinataire_id).first()
    if not db_destinataire:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Destinataire non trouvé.")

    db_message = models.Message(
        expediteur_id=current_user.id,
        destinataire_id=message.destinataire_id,
        contenu=message.contenu,
        date_envoi=datetime.now() # S'assure que l'horodatage est défini
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)

    # Compléter les emails pour la réponse si nécessaire (sinon, Pydantic les laissera None)
    response_message = schemas.MessageResponse.model_validate(db_message)
    response_message.expediteur_email = current_user.email
    response_message.destinataire_email = db_destinataire.email

    return response_message

@router.get("/me/", response_model=List[schemas.MessageResponse])
def get_my_messages(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 100,
    is_read: Optional[bool] = Query(None, description="Filtrer par messages lus/non lus")
):
    """
    Récupère tous les messages envoyés par ou reçus par l'utilisateur actuel.
    """
    # Charger les messages où l'utilisateur est l'expéditeur ou le destinataire
    query = db.query(models.Message).options(
        joinedload(models.Message.expediteur), # Charger les informations de l'expéditeur
        joinedload(models.Message.destinataire) # Charger les informations du destinataire
    ).filter(
        (models.Message.expediteur_id == current_user.id) | (models.Message.destinataire_id == current_user.id)
    )

    if is_read is not None:
        query = query.filter(models.Message.lu == is_read)

    messages = query.order_by(models.Message.date_envoi.desc()).offset(skip).limit(limit).all()

    # Mapper les objets Message SQLAlchemy vers les schémas de réponse
    response_messages = []
    for msg in messages:
        msg_resp = schemas.MessageResponse.model_validate(msg)
        msg_resp.expediteur_email = msg.expediteur.email if msg.expediteur else None
        msg_resp.destinataire_email = msg.destinataire.email if msg.destinataire else None
        response_messages.append(msg_resp)

    return response_messages

@router.get("/conversation/{other_user_id}", response_model=List[schemas.MessageResponse])
def get_conversation(
    other_user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 100
):
    """
    Récupère la conversation entre l'utilisateur actuel et un autre utilisateur spécifique.
    """
    # Vérifier que l'autre utilisateur existe
    db_other_user = db.query(models.User).filter(models.User.id == other_user_id).first()
    if not db_other_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cet utilisateur n'existe pas.")

    query = db.query(models.Message).options(
        joinedload(models.Message.expediteur),
        joinedload(models.Message.destinataire)
    ).filter(
        # Messages envoyés par l'utilisateur actuel à l'autre utilisateur
        ((models.Message.expediteur_id == current_user.id) & (models.Message.destinataire_id == other_user_id)) |
        # Messages envoyés par l'autre utilisateur à l'utilisateur actuel
        ((models.Message.expediteur_id == other_user_id) & (models.Message.destinataire_id == current_user.id))
    )

    conversation = query.order_by(models.Message.date_envoi).offset(skip).limit(limit).all()

    response_conversation = []
    for msg in conversation:
        msg_resp = schemas.MessageResponse.model_validate(msg)
        msg_resp.expediteur_email = msg.expediteur.email if msg.expediteur else None
        msg_resp.destinataire_email = msg.destinataire.email if msg.destinataire else None
        response_conversation.append(msg_resp)

    return response_conversation


@router.put("/{message_id}/read", response_model=schemas.MessageResponse)
def mark_message_as_read(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Marque un message spécifique comme lu.
    Seul le destinataire du message peut le marquer comme lu.
    """
    db_message = db.query(models.Message).filter(models.Message.id == message_id).first()

    if db_message is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message non trouvé.")

    # S'assurer que seul le destinataire peut marquer le message comme lu
    if db_message.destinataire_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vous n'êtes pas autorisé à marquer ce message comme lu.")

    db_message.lu = True
    db.commit()
    db.refresh(db_message)

    # Compléter les emails pour la réponse
    response_message = schemas.MessageResponse.model_validate(db_message)
    response_message.expediteur_email = db_message.expediteur.email if db_message.expediteur else None
    response_message.destinataire_email = db_message.destinataire.email if db_message.destinataire else None

    return response_message

@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_message(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Supprime un message. Seul l'expéditeur peut supprimer ses propres messages.
    """
    db_message = db.query(models.Message).filter(models.Message.id == message_id).first()

    if db_message is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message non trouvé.")

    # S'assurer que seul l'expéditeur peut supprimer le message
    if db_message.expediteur_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vous n'êtes pas autorisé à supprimer ce message.")

    db.delete(db_message)
    db.commit()
    return None