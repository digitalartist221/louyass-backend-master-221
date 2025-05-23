# app/auth/jwt.py

from jose import jwt, JWTError
from datetime import datetime, timedelta

# Clé secrète à garder confidentielle
SECRET_KEY = "SallEtSene"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Générer un JWT avec une date d'expiration
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
