from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.alerte import Alerte
from app.schemas.alerte import AlerteRead, AlerteResoudre
from app.services.alert_service import verifier_lots_anciens

router = APIRouter(prefix="/api/alertes", tags=["alertes"])


@router.get("", response_model=list[AlerteRead])
def list_alertes(db: Session = Depends(get_db)):
    return db.query(Alerte).order_by(Alerte.created_at.desc()).all()


@router.get("/{alerte_id}", response_model=AlerteRead)
def get_alerte(alerte_id: int, db: Session = Depends(get_db)):
    alerte = db.query(Alerte).filter(Alerte.id == alerte_id).first()
    if not alerte:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alerte introuvable")
    return alerte


@router.put("/{alerte_id}/resoudre", response_model=AlerteRead)
def resoudre_alerte(alerte_id: int, payload: AlerteResoudre, db: Session = Depends(get_db)):
    alerte = db.query(Alerte).filter(Alerte.id == alerte_id).first()
    if not alerte:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alerte introuvable")
    alerte.statut = payload.statut
    db.commit()
    db.refresh(alerte)
    return alerte


@router.post("/check-lots-anciens", response_model=list[AlerteRead])
def check_lots_anciens(db: Session = Depends(get_db)):
    return verifier_lots_anciens(db)
