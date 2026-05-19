import os
from dotenv import load_dotenv

load_dotenv()

APP_ENV = os.getenv("APP_ENV", "development").lower()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./avis.db")

CORS_ORIGINS = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "").split(",") if origin.strip()]

if APP_ENV != "production" and not CORS_ORIGINS:
    CORS_ORIGINS = [
        "https://avisclient.netlify.app",  # ← domaine racine, sans chemin
        "http://127.0.0.1:5501",
        "http://localhost:5500",
        "http://127.0.0.1:3000",
        "http://localhost:3000",
        "http://127.0.0.1:8000",
        "null",  # file://
    ]

DEBUG = APP_ENV != "production"
