# app/main.py

from fastapi import FastAPI
from app.auth.routes import router as auth_router
from app.database import Base, engine

from fastapi.middleware.cors import CORSMiddleware # Import CORSMiddleware
# Initialisation des tables de la base de données
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Hebergement - Backend API")

# Configure CORS
origins = [
    "http://localhost:3000",  # Allow your React frontend (CRA default)
    "http://localhost:5173",  # Allow your React frontend (Vite default)
    # Add any other origins where your frontend might be hosted, e'g'
    # "http://127.0.0.1:3000",
    # "http://127.0.0.1:5173",
    # "http://your-production-frontend-domain.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # List of allowed origins
    allow_credentials=True,      # Allow cookies to be sent with requests (important for authentication)
    allow_methods=["*"],         # Allow all HTTP methods (GET, POST, PUT, DELETE, OPTIONS, etc.)
    allow_headers=["*"],         # Allow all headers (e.g., Authorization header for JWT)
)


# Inclusion des routes d'authentification
app.include_router(auth_router)