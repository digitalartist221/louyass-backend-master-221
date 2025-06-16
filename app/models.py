from sqlalchemy import Column, Integer, String, Boolean, Float, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base  # Assure-toi que Base = declarative_base()

# --- Utilisateur ---
class User(Base):
    __tablename__ = "users"
    nom = Column(String, nullable=False)
    prenom = Column(String, nullable=False)
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    nom_utilisateur = Column(String, nullable=True)
    telephone = Column(String, nullable=True)
    cni = Column(Integer, unique=True, nullable=True)
    role = Column(String, nullable=False)  # proprietaire | locataire
    password = Column(String, nullable=False)
    cree_le = Column(DateTime, default=datetime.utcnow)

    maisons = relationship("Maison", back_populates="proprietaire")
    contrats = relationship("Contrat", back_populates="locataire")
    rendezvous = relationship("RendezVous", back_populates="locataire")
    problemes_signales = relationship("Probleme", back_populates="signaleur")


# --- Maison ---
class Maison(Base):
    __tablename__ = "maisons"
    nom = Column(String, nullable=False)
    id = Column(Integer, primary_key=True, index=True)
    adresse = Column(String, nullable=False)
    ville = Column(String, nullable=False)
    superficie = Column(Integer, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    description = Column(String, nullable=True)
    proprietaire_id = Column(Integer, ForeignKey("users.id"))
    cree_le = Column(DateTime, default=datetime.utcnow)

    proprietaire = relationship("User", back_populates="maisons")
    chambres = relationship("Chambre", back_populates="maison")


# --- Chambre ---
class Chambre(Base):
    __tablename__ = "chambres"

    id = Column(Integer, primary_key=True, index=True)
    maison_id = Column(Integer, ForeignKey("maisons.id"))
    titre = Column(String, nullable=False)
    description = Column(String, nullable=True)
    taille = Column(String, nullable=True)
    type = Column(String, nullable=False)  # simple | appartement | maison
    meublee = Column(Boolean, default=False)
    salle_de_bain = Column(Boolean, default=False)
    prix = Column(Float, nullable=False)
    disponible = Column(Boolean, default=True)
    cree_le = Column(DateTime, default=datetime.utcnow)
    capacite = Column(Integer, nullable=False)
    maison = relationship("Maison", back_populates="chambres")
    contrats = relationship("Contrat", back_populates="chambre")
    medias = relationship("Media", back_populates="chambre")
    rendezvous = relationship("RendezVous", back_populates="chambre", lazy='noload')


# --- Contrat ---
class Contrat(Base):
    __tablename__ = "contrats"

    id = Column(Integer, primary_key=True, index=True)
    locataire_id = Column(Integer, ForeignKey("users.id"))
    chambre_id = Column(Integer, ForeignKey("chambres.id"))
    date_debut = Column(Date, nullable=False)
    date_fin = Column(Date, nullable=False)
    montant_caution = Column(Float, nullable=False)
    mois_caution = Column(Integer, nullable=False)
    description = Column(String, nullable=True)
    mode_paiement = Column(String, nullable=False)  # virement | cash | mobile money
    periodicite = Column(String, nullable=False)  # journalier | mensuel...
    statut = Column(String, nullable=False)  # actif | resilié
    cree_le = Column(DateTime, default=datetime.utcnow)

    locataire = relationship("User", back_populates="contrats")
    chambre = relationship("Chambre", back_populates="contrats")
    paiements = relationship("Paiement", back_populates="contrat")
    problemes = relationship("Probleme", back_populates="contrat")


# --- Paiement ---
class Paiement(Base):
    __tablename__ = "paiements"

    id = Column(Integer, primary_key=True, index=True)
    contrat_id = Column(Integer, ForeignKey("contrats.id"))
    montant = Column(Float, nullable=False)
    statut = Column(String, nullable=False)  # payé | impayé
    date_echeance = Column(Date, nullable=False)
    date_paiement = Column(DateTime, nullable=True)
    cree_le = Column(DateTime, default=datetime.utcnow)

    contrat = relationship("Contrat", back_populates="paiements")


# --- RendezVous ---
class RendezVous(Base):
    __tablename__ = "rendezvous"

    id = Column(Integer, primary_key=True, index=True)
    locataire_id = Column(Integer, ForeignKey("users.id"))
    chambre_id = Column(Integer, ForeignKey("chambres.id"))
    date_heure = Column(DateTime, nullable=False)
    statut = Column(String, nullable=False)  # en_attente | confirmé | annulé
    cree_le = Column(DateTime, default=datetime.utcnow)
 
    locataire = relationship("User", back_populates="rendezvous", lazy='joined')
    chambre = relationship("Chambre", back_populates="rendezvous", lazy='noload')


# --- Media ---
class Media(Base):
    __tablename__ = "medias"

    id = Column(Integer, primary_key=True, index=True)
    chambre_id = Column(Integer, ForeignKey("chambres.id"))
    url = Column(String, nullable=False)
    type = Column(String, nullable=False)  # photo | video
    description = Column(String, nullable=True)
    cree_le = Column(DateTime, default=datetime.utcnow)

    chambre = relationship("Chambre", back_populates="medias")


# --- Probleme ---
class Probleme(Base):
    __tablename__ = "problemes"

    id = Column(Integer, primary_key=True, index=True)
    contrat_id = Column(Integer, ForeignKey("contrats.id"))
    signale_par = Column(Integer, ForeignKey("users.id"))
    description = Column(String, nullable=False)
    type = Column(String, nullable=False)  # plomberie | electricite | autre
    responsable = Column(String, nullable=False)  # locataire | proprietaire
    resolu = Column(Boolean, default=False)
    cree_le = Column(DateTime, default=datetime.utcnow)

    contrat = relationship("Contrat", back_populates="problemes")
    signaleur = relationship("User", back_populates="problemes_signales")
