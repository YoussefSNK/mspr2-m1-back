from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.mesure import Mesure
from app.schemas.mesure import MesureCreate, MesureRead
from app.services.alert_service import traiter_mesure_alertes

router = APIRouter(prefix="/api/mesures", tags=["mesures"])


@router.get("", response_model=list[MesureRead])
def list_mesures(
    pays: str | None = Query(None),
    entrepot: str | None = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(Mesure)
    if pays:
        q = q.filter(Mesure.pays == pays.lower())
    if entrepot:
        q = q.filter(Mesure.entrepot == entrepot)
    return q.order_by(Mesure.date_mesure.desc()).all()


@router.post("", response_model=MesureRead, status_code=status.HTTP_201_CREATED)
def create_mesure(payload: MesureCreate, db: Session = Depends(get_db)):
    mesure = Mesure(
        pays=payload.pays,
        entrepot=payload.entrepot,
        temperature=payload.temperature,
        humidite=payload.humidite,
        statut=payload.statut,
        date_mesure=payload.date_mesure,
        lot_id=payload.lot_id,
    )
    db.add(mesure)
    db.commit()
    db.refresh(mesure)

    traiter_mesure_alertes(
        db,
        mesure.pays,
        mesure.entrepot,
        mesure.temperature,
        mesure.humidite,
        mesure.id,
    )
    return mesure
