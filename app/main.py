from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.routes import router as auth_router

# IMPORTER LES ROUTEURS DIRECTEMENT DEPUIS LEURS FICHIERS RESPECTIFS
from app.routers.users import router as users_router
from app.routers.maisons import router as maisons_router
from app.routers.chambres import router as chambres_router
from app.routers.contrats import router as contrats_router
from app.routers.paiements import router as paiements_router
from app.routers.rendez_vous import router as rendez_vous_router
from app.routers.medias import router as medias_router
from app.routers.problemes import router as problemes_router
from app.routers.recherche import router as recherche_router # <-- AJOUTEZ CETTE LIGNE

from app.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Hebergement - API Backend")

# Configurer CORS
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)

# INCLUSION DES NOUVEAUX ROUTEURS CRUD
app.include_router(users_router)
app.include_router(maisons_router)
app.include_router(chambres_router)
app.include_router(contrats_router)
app.include_router(paiements_router)
app.include_router(rendez_vous_router)
app.include_router(medias_router)
app.include_router(problemes_router)
app.include_router(recherche_router) # <-- AJOUTEZ CETTE LIGNE


@app.get("/")
def read_root():
    return {"message": "Bienvenue sur l'API Backend de Hebergement"}