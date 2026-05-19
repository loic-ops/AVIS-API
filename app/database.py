from sqlalchemy import create_engine, Column, Integer, Float, String, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from app.config import DATABASE_URL

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL, future=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class AvisModel(Base):
    __tablename__ = "avis"
    
    id = Column(Integer, primary_key=True, index=True)
    note = Column(Integer, nullable=True)
    accueil = Column(Float, nullable=True)
    examen = Column(Float, nullable=True)
    ecoute = Column(Float, nullable=True)
    explications = Column(Float, nullable=True)
    attente = Column(Float, nullable=True)
    tags = Column(JSON, default=[])
    commentaire = Column(Text, nullable=True)
    recommandation = Column(String(50), nullable=True)

    statut = Column(String(20), default="nouveau")

    created_at = Column(DateTime, default=datetime.now)

class AdminConfig(Base):
    __tablename__ = "admin_config"
    
    id = Column(Integer, primary_key=True, index=True)
    admin_code = Column(String(6), nullable=False)
    responsable_name = Column(String(100), default="Responsable")
    created_at = Column(DateTime, default=datetime.now)

# Créer les tables
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
