from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class StatutEnum(str, Enum):
    nouveau = "nouveau"
    lu = "lu"
    traite = "traite"

class RecommandationEnum(str, Enum):
    oui = "oui"
    peut_etre = "peut-etre"
    non = "non"


class AvisCreate(BaseModel):
    note: Optional[int] = Field(None, ge=1, le=5, description="Note de 1 à 5")
    accueil: Optional[float] = Field(None, ge=1, le=5)
    examen: Optional[float] = Field(None, ge=1, le=5)
    ecoute: Optional[float] = Field(None, ge=1, le=5)
    explications: Optional[float] = Field(None, ge=1, le=5)
    attente: Optional[float] = Field(None, ge=1, le=5)
    tags: List[str] = Field(default_factory=list)
    commentaire: Optional[str] = None
    recommandation: Optional[RecommandationEnum] = None

class AvisUpdate(BaseModel):
    statut: Optional[StatutEnum] = None

class AvisResponse(BaseModel):
    id: int
    note: Optional[int]
    accueil: Optional[float]
    examen: Optional[float]
    ecoute: Optional[float]
    explications: Optional[float]
    attente: Optional[float]
    tags: List[str]
    commentaire: Optional[str]
    recommandation: Optional[str]
    statut: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class StatsResponse(BaseModel):
    avg_rating: float
    total: int
    new_count: int
    reco_pct: float
    reco_yes: int
    reco_maybe: int
    reco_no: int
    criteres: dict
    distribution: dict
