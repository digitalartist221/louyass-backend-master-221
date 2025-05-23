# app/schemas.py

from pydantic import BaseModel, EmailStr

# Schéma pour l'inscription (entrée)
class UserCreate(BaseModel):
    email: EmailStr
    password: str

# Schéma pour la réponse (sortie)
class UserResponse(BaseModel):
    id: int
    email: EmailStr

    class Config:
        orm_mode = True  # Permet d'utiliser des objets SQLAlchemy
