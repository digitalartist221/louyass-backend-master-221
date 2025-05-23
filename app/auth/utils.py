# app/auth/utils.py

from passlib.context import CryptContext

# Contexte pour hachage avec l'algorithme bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hacher un mot de passe en clair
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# Vérifier un mot de passe contre son haché
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
