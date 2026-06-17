from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.lot import Lot
from app.schemas.lot import LotCreate, LotRead, LotUpdate

router = APIRouter(prefix="/api/lots", tags=["lots"])


@router.get("", response_model=list[LotRead])
def list_lots(db: Session = Depends(get_db)):
    return db.query(Lot).order_by(Lot.date_stockage).all()


@router.get("/fifo", response_model=list[LotRead])
def fifo_lots(db: Session = Depends(get_db)):
    return (
        db.query(Lot)
        .filter(Lot.statut.in_(["conforme", "en_alerte"]))
        .order_by(Lot.date_stockage)
        .all()
    )


@router.get("/{lot_id}", response_model=LotRead)
def get_lot(lot_id: int, db: Session = Depends(get_db)):
    lot = db.query(Lot).filter(Lot.id == lot_id).first()
    if not lot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lot introuvable")
    return lot


@router.post("", response_model=LotRead, status_code=status.HTTP_201_CREATED)
def create_lot(payload: LotCreate, db: Session = Depends(get_db)):
    existing = db.query(Lot).filter(Lot.lot_code == payload.lot_code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Lot avec code {payload.lot_code!r} existe déjà",
        )
    lot = Lot(**payload.model_dump())
    db.add(lot)
    db.commit()
    db.refresh(lot)
    return lot


@router.put("/{lot_id}", response_model=LotRead)
def update_lot(lot_id: int, payload: LotUpdate, db: Session = Depends(get_db)):
    lot = db.query(Lot).filter(Lot.id == lot_id).first()
    if not lot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lot introuvable")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(lot, field, value)
    db.commit()
    db.refresh(lot)
    return lot


@router.delete("/{lot_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lot(lot_id: int, db: Session = Depends(get_db)):
    lot = db.query(Lot).filter(Lot.id == lot_id).first()
    if not lot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lot introuvable")
    db.delete(lot)
    db.commit()
