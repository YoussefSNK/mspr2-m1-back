from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.lot import Lot
from app.models.mesure import Mesure
from app.schemas.mesure import MesureRead

router = APIRouter(prefix="/api/lots", tags=["lots-mesures"])


@router.get("/{lot_id}/mesures", response_model=list[MesureRead])
def get_mesures_lot(lot_id: int, db: Session = Depends(get_db)):
    lot = db.query(Lot).filter(Lot.id == lot_id).first()
    if not lot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lot introuvable")
    return (
        db.query(Mesure)
        .filter(Mesure.lot_id == lot_id)
        .order_by(Mesure.date_mesure)
        .all()
    )
