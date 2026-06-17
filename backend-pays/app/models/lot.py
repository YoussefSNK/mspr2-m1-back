from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class Lot(Base):
    __tablename__ = "lots"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    lot_code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    pays: Mapped[str] = mapped_column(String(50), nullable=False)
    exploitation: Mapped[str] = mapped_column(String(100), nullable=False)
    entrepot: Mapped[str] = mapped_column(String(100), nullable=False)
    date_stockage: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    statut: Mapped[str] = mapped_column(String(20), nullable=False, default="conforme")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("ix_lots_pays", "pays"),
        Index("ix_lots_date_stockage", "date_stockage"),
        Index("ix_lots_statut", "statut"),
    )
