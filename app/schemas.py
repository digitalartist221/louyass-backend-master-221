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

class MaisonResponse(BaseModel):
    id: int
    proprietaire_id: int
    nom: str
    adresse: str
    ville: str
    superficie: Optional[float] # Or int, depending on your data type. Make sure it's here and required.
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: Optional[str] = None
    cree_le: datetime

    class Config:
        from_attributes = True # Or orm_mode = True for Pydantic v1
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

# Schéma pour les détails de la Maison, à inclure dans la Chambre détaillée
class MaisonDetails(BaseModel):
    id: int
    nom: str
    adresse: str
    ville: str
    superficie: Optional[float] = None
    latitude: Optional[float] = None # Ajout de la latitude
    longitude: Optional[float] = None # Ajout de la longitude

    class Config:
        from_attributes = True

# Schéma pour les détails d'un média de chambre
class ChambreMediaSchema(BaseModel):
    id: int
    url: str
    description: Optional[str] = None
    est_principale: bool = False

    class Config:
        from_attributes = True

# Schéma pour la réponse détaillée de la chambre
class ChambreResponseDetailed(BaseModel):
    id: int
    titre: str
    description: Optional[str] = None
    prix: float
    type: str
    capacite: int
    taille: Optional[float] = None
    salle_de_bain: bool
    meublee: bool
    disponible: bool
    cree_le: datetime
    maison_id: int
    maison: Optional[MaisonDetails] = None # Inclure les détails de la maison
    medias: List[ChambreMediaSchema] = [] # Inclure la liste des médias

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

# --- Rendez-vous Schemas ---
class RendezVousCreate(BaseModel):
    locataire_id: int
    chambre_id: int
    date_heure: datetime
    statut: str = Field(default="en_attente")
    # propose_nouvelle_date n'est pas inclus ici car c'est pour la modification par le propriétaire

class RendezVousUpdate(BaseModel): # Nouveau schéma pour les mises à jour
    statut: Optional[str] = None
    date_heure: Optional[datetime] = None # Si le locataire modifie la date/heure

class SimpleUserResponse(BaseModel):
    id: int
    nom: str
    email: EmailStr

    class Config:
        from_attributes = True

class RendezVousResponse(BaseModel):
    id: int
    locataire_id: int
    chambre_id: int
    date_heure: datetime
    statut: str
    cree_le: datetime
    locataire: Optional[SimpleUserResponse] = None
    chambre: Optional[ChambreResponse] = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }
        json_loads = lambda x: x
        json_dumps = lambda x: x
        json_schema_extra = {
            "example": {
                "id": 1,
                "locataire_id": 1,
                "chambre_id": 1,
                "date_heure": "2025-06-14T19:08:53+02:00",
                "statut": "en_attente",
                "cree_le": "2025-06-14T19:08:53+02:00",
                "locataire": {
                    "id": 1,
                    "nom": "John Doe",
                    "email": "john@example.com"
                },
                "chambre": {
                    "id": 1,
                    "titre": "Chambre confortable",
                    "prix": 500.0,
                    "maison": {
                        "id": 1,
                        "adresse": "123 Rue de Paris",
                        "ville": "Paris"
                    }
                }
            }
        }
   
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
# --- Message de notification (pour l'email) ---
class EmailMessage(BaseModel):
    destinataire_email: str
    sujet: str
    corps: str


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
    locataire: Optional[SimpleUserResponse] = None # Optional, based on your backend logic
    chambre: Optional[ChambreResponse] = None     # Optional, based on your backend logic

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
        from_attributes = True # Très important pour la conversion automatiqu