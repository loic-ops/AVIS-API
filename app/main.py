from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, List
from pydantic import BaseModel
import json
import secrets

from app.config import CORS_ORIGINS
from app.database import get_db, AvisModel, AdminConfig
from app.models import AvisCreate, AvisUpdate, AvisResponse, StatsResponse, StatutEnum

app = FastAPI(title="OpticiCritique API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

# ─── MODELS ADMIN ──────────────────────────────────────

class AdminVerifyRequest(BaseModel):
    code: str

class AdminChangeCodeRequest(BaseModel):
    old_code: str
    new_code: str

class AdminAuthResponse(BaseModel):
    token: str
    message: str

# ─── ENDPOINTS ADMIN ──────────────────────────────────────

def init_admin_code(db: Session):
    """Initialiser le code admin par défaut si absent"""
    admin = db.query(AdminConfig).first()
    if not admin:
        admin = AdminConfig(admin_code="000000")
        db.add(admin)
        db.commit()
    return admin

@app.post("/api/admin/verify", response_model=AdminAuthResponse)
def verify_admin_code(req: AdminVerifyRequest, db: Session = Depends(get_db)):
    """Vérifier le code admin et retourner un token"""
    admin = db.query(AdminConfig).first()
    if not admin:
        admin = init_admin_code(db)
    
    if req.code != admin.admin_code:
        raise HTTPException(status_code=401, detail="Code incorrect")
    
    # Générer un token simple (en production, utiliser JWT)
    token = secrets.token_urlsafe(32)
    
    return AdminAuthResponse(
        token=token,
        message="Authentification réussie"
    )

@app.post("/api/admin/change-code")
def change_admin_code(req: AdminChangeCodeRequest, db: Session = Depends(get_db)):
    """Changer le code admin"""
    if len(req.new_code) != 6 or not req.new_code.isdigit():
        raise HTTPException(status_code=400, detail="Le code doit être 6 chiffres")
    
    admin = db.query(AdminConfig).first()
    if not admin:
        admin = init_admin_code(db)
    
    if req.old_code != admin.admin_code:
        raise HTTPException(status_code=401, detail="Ancien code incorrect")
    
    admin.admin_code = req.new_code
    db.commit()
    
    return {"message": "Code modifié avec succès"}

@app.get("/api/admin/profile")
def get_admin_profile(db: Session = Depends(get_db)):
    """Récupérer les infos du profil admin"""
    admin = db.query(AdminConfig).first()
    if not admin:
        admin = init_admin_code(db)
    
    return {
        "responsable_name": admin.responsable_name,
        "created_at": admin.created_at
    }

# ─── ENDPOINTS ──────────────────────────────────────────

@app.post("/api/avis", response_model=AvisResponse, status_code=201)
def create_avis(avis: AvisCreate, db: Session = Depends(get_db)):
    """
    Créer un nouvel avis patient.
    """
    new_avis = AvisModel(
        note=avis.note,
        accueil=avis.accueil,
        examen=avis.examen,
        ecoute=avis.ecoute,
        explications=avis.explications,
        attente=avis.attente,
        tags=avis.tags,
        commentaire=avis.commentaire,
        recommandation=avis.recommandation.value if avis.recommandation else None,
        statut="nouveau",
        created_at=datetime.now()
    )
    db.add(new_avis)
    db.commit()
    db.refresh(new_avis)
    return new_avis

@app.get("/api/avis", response_model=List[AvisResponse])
def list_avis(
    statut: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=9999),
    order: str = Query("desc", regex="^(asc|desc)$"),
    period: Optional[int] = Query(None, description="Jours depuis maintenant"),
    db: Session = Depends(get_db)
):
    """
    Récupérer la liste des avis avec filtres optionnels.
    - statut: filtrer par statut (nouveau/lu/traite)
    - limit: nombre d'avis à retourner
    - order: ordre (asc/desc)
    - period: avis des N derniers jours
    """
    query = db.query(AvisModel)
    
    # Filtrer par statut
    if statut:
        query = query.filter(AvisModel.statut == statut)
    
    # Filtrer par période
    if period:
        since = datetime.now() - timedelta(days=period)
        query = query.filter(AvisModel.created_at >= since)
    
    # Trier
    if order == "asc":
        query = query.order_by(AvisModel.created_at.asc())
    else:
        query = query.order_by(AvisModel.created_at.desc())
    
    # Limiter
    query = query.limit(limit)
    
    avis_list = query.all()
    return avis_list

@app.get("/api/avis/{avis_id}", response_model=AvisResponse)
def get_avis(avis_id: int, db: Session = Depends(get_db)):
    """
    Récupérer un avis par son ID.
    """
    avis = db.query(AvisModel).filter(AvisModel.id == avis_id).first()
    if not avis:
        raise HTTPException(status_code=404, detail="Avis non trouvé")
    return avis

@app.put("/api/avis/{avis_id}", response_model=AvisResponse)
def update_avis_statut(
    avis_id: int,
    update: AvisUpdate,
    db: Session = Depends(get_db)
):
    """
    Mettre à jour le statut d'un avis (nouveau/lu/traite).
    """
    avis = db.query(AvisModel).filter(AvisModel.id == avis_id).first()
    if not avis:
        raise HTTPException(status_code=404, detail="Avis non trouvé")

    if update.statut:
        avis.statut = update.statut.value

    db.commit()
    db.refresh(avis)
    return avis


class StatutPayload(BaseModel):
    statut: str


@app.patch("/api/avis/{avis_id}/status", response_model=AvisResponse)
def patch_avis_status(
    avis_id: int,
    payload: StatutPayload,
    db: Session = Depends(get_db)
):
    """Alias compatible avec reviews.html.

    Corps attendu: {"statut": "nouveau|lu|traite|archive"}
    """
    avis = db.query(AvisModel).filter(AvisModel.id == avis_id).first()
    if not avis:
        raise HTTPException(status_code=404, detail="Avis non trouvé")

    avis.statut = payload.statut
    db.commit()
    db.refresh(avis)
    return avis


class AvisNoteAdminPatch(BaseModel):
    note_admin: Optional[str] = None


@app.patch("/api/avis/{avis_id}/note")
def patch_avis_note_admin(
    avis_id: int,
    payload: AvisNoteAdminPatch,
    db: Session = Depends(get_db)
):
    """Alias compatible avec reviews.html.

    Stocke une note interne côté admin. (La colonne n'existe pas encore dans le modèle actuel.)
    """
    avis = db.query(AvisModel).filter(AvisModel.id == avis_id).first()
    if not avis:
        raise HTTPException(status_code=404, detail="Avis non trouvé")

    # Champ dynamique si présent
    if hasattr(AvisModel, 'note_admin'):
        avis.note_admin = payload.note_admin

    db.commit()
    db.refresh(avis)
    return avis


@app.get("/api/stats", response_model=StatsResponse)
def get_stats(
    period: Optional[int] = Query(30, description="Nombre de jours"),
    db: Session = Depends(get_db)
):
    """
    Récupérer les statistiques des avis pour le tableau de bord.
    """
    # Filtrer par période
    since = datetime.now() - timedelta(days=period)
    avis_list = db.query(AvisModel).filter(AvisModel.created_at >= since).all()
    
    # Si pas d'avis, retourner stats vides
    if not avis_list:
        return StatsResponse(
            avg_rating=0,
            total=0,
            new_count=0,
            reco_pct=0,
            reco_yes=0,
            reco_maybe=0,
            reco_no=0,
            criteres={
                "accueil": 0,
                "examen": 0,
                "ecoute": 0,
                "explications": 0,
                "attente": 0
            },
            distribution={1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        )
    
    # Calcul des stats
    total = len(avis_list)
    new_count = len([a for a in avis_list if a.statut == "nouveau"])
    
    # Note moyenne uniquement sur les avis contenant une note
    note_values = [a.note for a in avis_list if a.note is not None]
    avg_rating = round(sum(note_values) / len(note_values), 1) if note_values else 0
    
    # Critères moyens - moyenne sur les valeurs renseignées seulement
    criteres = {
        "accueil": round(sum(a.accueil for a in avis_list if a.accueil is not None) / len([a for a in avis_list if a.accueil is not None]), 1) if any(a.accueil is not None for a in avis_list) else 0,
        "examen": round(sum(a.examen for a in avis_list if a.examen is not None) / len([a for a in avis_list if a.examen is not None]), 1) if any(a.examen is not None for a in avis_list) else 0,
        "ecoute": round(sum(a.ecoute for a in avis_list if a.ecoute is not None) / len([a for a in avis_list if a.ecoute is not None]), 1) if any(a.ecoute is not None for a in avis_list) else 0,
        "explications": round(sum(a.explications for a in avis_list if a.explications is not None) / len([a for a in avis_list if a.explications is not None]), 1) if any(a.explications is not None for a in avis_list) else 0,
        "attente": round(sum(a.attente for a in avis_list if a.attente is not None) / len([a for a in avis_list if a.attente is not None]), 1) if any(a.attente is not None for a in avis_list) else 0,
    }
    
    # Distribution des notes (1-5)
    distribution = {
        1: len([a for a in avis_list if a.note == 1]),
        2: len([a for a in avis_list if a.note == 2]),
        3: len([a for a in avis_list if a.note == 3]),
        4: len([a for a in avis_list if a.note == 4]),
        5: len([a for a in avis_list if a.note == 5]),
    }
    
    # Recommandation
    reco_yes = len([a for a in avis_list if a.recommandation == "oui"])
    reco_maybe = len([a for a in avis_list if a.recommandation == "peut-etre"])
    reco_no = len([a for a in avis_list if a.recommandation == "non"])
    reco_pct = round((reco_yes / total * 100), 0) if total > 0 else 0
    
    return StatsResponse(
        avg_rating=round(avg_rating, 1),
        total=total,
        new_count=new_count,
        reco_pct=int(reco_pct),
        reco_yes=reco_yes,
        reco_maybe=reco_maybe,
        reco_no=reco_no,
        criteres=criteres,
        distribution=distribution
    )

@app.delete("/api/avis/{avis_id}", status_code=204)
def delete_avis(avis_id: int, db: Session = Depends(get_db)):
    """
    Supprimer un avis.
    """
    avis = db.query(AvisModel).filter(AvisModel.id == avis_id).first()
    if not avis:
        raise HTTPException(status_code=404, detail="Avis non trouvé")
    
    db.delete(avis)
    db.commit()
    return None

@app.get("/")
def root():
    """
    Health check
    """
    return {"message": "OpticiCritique API running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
