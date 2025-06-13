from datetime import date, datetime
from typing import Optional, List, ForwardRef
from pydantic import BaseModel, EmailStr, Field
from fastapi import UploadFile
from app.models import User

# Forward references pour les dépendances circulaires
ChambreResponse = ForwardRef('ChambreResponse')
ContratResponse = ForwardRef('ContratResponse')
MediaResponse = ForwardRef('MediaResponse')
RendezVousResponse = ForwardRef('RendezVousResponse')
MaisonResponse = ForwardRef('MaisonResponse')

# --- User Schemas ---
class UserLogin(BaseModel):
    email: str
    password: str

class UserBase(BaseModel):
    nom: str
    prenom: str
    email: EmailStr
    nom_utilisateur: Optional[str] = None
    telephone: Optional[str] = None
    cni: Optional[int] = None
    role: str  # proprietaire | locataire

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    cree_le: datetime

    class Config:
        from_attributes = True

# --- House Schemas ---
class MaisonBase(BaseModel):
    adresse: str
    ville: str
    superficie: int
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: Optional[str] = None

class MaisonCreate(MaisonBase):
    proprietaire_id: int

class MaisonResponse(MaisonBase):
    id: int
    proprietaire_id: int
    cree_le: datetime

    class Config:
        from_attributes = True

# --- Room Schemas ---
class ChambreBase(BaseModel):
    maison_id: int
    titre: str
    description: Optional[str] = None
    taille: Optional[str] = None  # ex: 12m²
    type: str  # simple | appartement | maison
    meublee: bool
    prix: Optional[float] = None
    disponibilite: Optional[bool] = None
    capacite: Optional[int] = None
    caracteristiques: Optional[list] = None
    images: Optional[list] = None
    salle_de_bain: bool
    disponible: bool = True

class ChambreCreate(ChambreBase):
    pass

class ChambreResponse(ChambreBase):
    id: int
    cree_le: datetime
    maison: MaisonResponse
    contrats: List[ContratResponse] = []
    rendezvous: List[RendezVousResponse] = []
    medias: List[MediaResponse] = []

    class Config:
        from_attributes = True

# --- Contract Schemas ---
class ContratBase(BaseModel):
    locataire_id: int
    chambre_id: int
    date_debut: date
    date_fin: date
    montant_caution: float
    mois_caution: int  # <= 3
    description: Optional[str] = None
    mode_paiement: str  # virement | cash | mobile money
    periodicite: str  # journalier | hebdomadaire | mensuel
    statut: str  # actif | resilié

class ContratCreate(ContratBase):
    pass

class ContratResponse(ContratBase):
    id: int
    cree_le: datetime

    class Config:
        from_attributes = True

# --- Payment Schemas ---
class PaiementBase(BaseModel):
    contrat_id: int
    montant: float
    statut: str  # payé | impayé
    date_echeance: date
    date_paiement: Optional[datetime] = None

class PaiementCreate(PaiementBase):
    pass

class PaiementResponse(PaiementBase):
    id: int
    cree_le: datetime

    class Config:
        from_attributes = True

# --- Appointment Schemas ---
class RendezVousBase(BaseModel):
    locataire_id: int
    chambre_id: int
    date_heure: datetime
    statut: str  # en_attente | confirmé | annulé

class RendezVousCreate(RendezVousBase):
    pass

class RendezVousResponse(RendezVousBase):
    id: int
    cree_le: datetime

    class Config:
        from_attributes = True

# --- Media Schemas ---
class MediaBase(BaseModel):
    chambre_id: int
    description: Optional[str] = None

class MediaCreate(BaseModel):
    file: UploadFile  # Champ pour le fichier à uploader
    type: str  # photo | video
    description: Optional[str] = None

class MediaResponse(MediaBase):
    id: int
    url: str
    type: str  # photo | video
    cree_le: datetime
    chambre: Optional[ChambreBase] = None  # Relation avec la chambre

    class Config:
        from_attributes = True

# --- Problem Schemas ---
class ProblemeBase(BaseModel):
    contrat_id: int
    signale_par: int  # utilisateur_id
    description: str
    type: str  # plomberie | electricite | autre
    responsable: str  # locataire | proprietaire
    resolu: bool = False

class ProblemeCreate(ProblemeBase):
    pass

class ProblemeResponse(ProblemeBase):
    id: int
    cree_le: datetime

    class Config:
        from_attributes = True

# --- Authentication Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None  # Email ou ID selon le contenu du token

# --- SCHÉMA PRINCIPAL POUR LES RÉSULTATS DE RECHERCHE ---
class RechercheResult(BaseModel):
    """
    Schéma combiné pour les résultats de recherche, pouvant représenter une maison ou une chambre.
    """
    id: int
    type_bien: str = Field(..., description="Indique si le résultat est une 'maison' ou une 'chambre'")
    adresse: str = Field(..., description="L'adresse de la maison associée à l'annonce")
    prix: float = Field(..., description="Le prix du bien (prix de la chambre si c'est une chambre, ou prix minimum estimé pour une maison)")
    description: Optional[str] = Field(None, description="Description générale du bien")
    details: dict = Field(..., description="Détails spécifiques au type de bien (chambre ou maison)")

    class Config:
        from_attributes = True

# Résolution des forward references
ChambreResponse.update_forward_refs()
ContratResponse.update_forward_refs()
MediaResponse.update_forward_refs()
RendezVousResponse.update_forward_refs()
MaisonResponse.update_forward_refs()
class UserLogin(BaseModel):
    email: str
    password: str
# --- User Schemas ---
class UserBase(BaseModel):
    nom: str
    prenom: str
    email: EmailStr
    nom_utilisateur: Optional[str] = None
    telephone: Optional[str] = None
    cni: Optional[int] = None
    role: str  # proprietaire | locataire

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    cree_le: datetime

    class Config:
        from_attributes = True

# --- House Schemas ---
class MaisonBase(BaseModel):
    nom: str
    adresse: str
    ville: str
    superficie: int
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: Optional[str] = None

class MaisonCreate(MaisonBase):
    proprietaire_id: int

class MaisonResponse(MaisonBase):
    id: int
    proprietaire_id: int
    cree_le: datetime

    class Config:
        from_attributes = True

# --- Room Schemas ---
class ChambreBase(BaseModel):
    maison_id: int
    titre: str
    description: Optional[str] = None
    taille: Optional[str] = None  # ex: 12m²
    type: str  # simple | appartement | maison
    meublee: bool
    prix: Optional[float] = None
    capacite: Optional[int] = None
    salle_de_bain: bool
    disponible: bool = True

class ChambreCreate(ChambreBase):
    pass

class ChambreResponse(ChambreBase):
    id: int
    cree_le: datetime
    maison_id: int
    maison: Optional[MaisonResponse] = None  # Relation avec la maison
    contrats: list[ContratResponse] = []  # Liste des contrats associés
    medias: list[MediaResponse] = []  # Liste des médias associés
    rendezvous: list[RendezVousResponse] = []  # Liste des rendez-vous associés

    class Config:
        from_attributes = True
        exclude = {'medias', 'contrats', 'rendezvous'}

# --- Contract Schemas ---
class ContratBase(BaseModel):
    locataire_id: int
    chambre_id: int
    date_debut: date
    date_fin: date
    montant_caution: float
    mois_caution: int  # <= 3
    description: Optional[str] = None
    mode_paiement: str  # virement | cash | mobile money
    periodicite: str  # journalier | hebdomadaire | mensuel
    statut: str  # actif | resilié

class ContratCreate(ContratBase):
    pass

class ContratResponse(ContratBase):
    id: int
    cree_le: datetime

    class Config:
        from_attributes = True

# --- Payment Schemas ---
class PaiementBase(BaseModel):
    contrat_id: int
    montant: float
    statut: str  # payé | impayé
    date_echeance: date
    date_paiement: Optional[datetime] = None

class PaiementCreate(PaiementBase):
    pass

class PaiementResponse(PaiementBase):
    id: int
    cree_le: datetime

    class Config:
        from_attributes = True

# --- Appointment Schemas ---
class RendezVousBase(BaseModel):
    locataire_id: int
    chambre_id: int
    date_heure: datetime
    statut: str  # en_attente | confirmé | annulé

class RendezVousCreate(RendezVousBase):
    pass

class RendezVousResponse(RendezVousBase):
    id: int
    cree_le: datetime

    class Config:
        from_attributes = True

# --- Media Schemas ---
class MediaBase(BaseModel):
    chambre_id: int
    description: Optional[str] = None

class MediaCreate(BaseModel):
    file: UploadFile  # Champ pour le fichier à uploader
    type: str  # photo | video
    description: Optional[str] = None

class MediaResponse(MediaBase):
    id: int
    url: str
    type: str  # photo | video
    cree_le: datetime
    
    class Config:
        from_attributes = True

# --- Problem Schemas ---
class ProblemeBase(BaseModel):
    contrat_id: int
    signale_par: int  # utilisateur_id
    description: str
    type: str  # plomberie | electricite | autre
    responsable: str  # locataire | proprietaire
    resolu: bool = False

class ProblemeCreate(ProblemeBase):
    pass

class ProblemeResponse(ProblemeBase):
    id: int
    cree_le: datetime

    class Config:
        from_attributes = True

# --- Authentication Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None  # Email ou ID selon le contenu du token

# --- SCHÉMA PRINCIPAL POUR LES RÉSULTATS DE RECHERCHE ---
class RechercheResult(BaseModel):
    """
    Schéma combiné pour les résultats de recherche, pouvant représenter une maison ou une chambre.
    """
    id: int
    type_bien: str = Field(..., description="Indique si le résultat est une 'maison' ou une 'chambre'")
    adresse: str = Field(..., description="L'adresse de la maison associée à l'annonce")
    prix: float = Field(..., description="Le prix du bien (prix de la chambre si c'est une chambre, ou prix minimum estimé pour une maison)")
    description: Optional[str] = Field(None, description="Description générale du bien")
    details: dict = Field(..., description="Détails spécifiques au type de bien (chambre ou maison)")

    class Config:
        from_attributes = True # Très important pour la conversion automatiqu