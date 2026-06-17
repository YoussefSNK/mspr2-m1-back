from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Float, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class Mesure(Base):
    __tablename__ = "mesures"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    pays: Mapped[str] = mapped_column(String(50), nullable=False)
    entrepot: Mapped[str] = mapped_column(String(100), nullable=False)
    temperature: Mapped[float] = mapped_column(Float, nullable=False)
    humidite: Mapped[float] = mapped_column(Float, nullable=False)
    statut: Mapped[str] = mapped_column(String(20), nullable=False, default="ok")
    date_mesure: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    lot_id: Mapped[int | None] = mapped_column(ForeignKey("lots.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("ix_mesures_pays", "pays"),
        Index("ix_mesures_entrepot", "entrepot"),
        Index("ix_mesures_date_mesure", "date_mesure"),
    )
