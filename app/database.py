# app/database.py

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# URL de la base de données SQLite (elle sera créée automatiquement si elle n'existe pas)
SQLALCHEMY_DATABASE_URL = "sqlite:///./airbnb.db"

# Création du moteur de connexion SQLite
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Création d'une session de base de données
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base commune pour tous les modèles (User, Booking, etc.)
Base = declarative_base()

# Fonction utilitaire pour obtenir une session dans les routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
