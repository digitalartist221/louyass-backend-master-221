# app/models.py

from sqlalchemy import Column, Integer, String
from .database import Base

# Modèle SQLAlchemy pour représenter un utilisateur
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)  # Identifiant unique
    email = Column(String, unique=True, index=True)     # Email unique
    hashed_password = Column(String)                    # Mot de passe haché
