from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class Alerte(Base):
    __tablename__ = "alertes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    type_alerte: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    niveau: Mapped[str] = mapped_column(String(20), nullable=False, default="warning")
    pays: Mapped[str] = mapped_column(String(50), nullable=False)
    entrepot: Mapped[str | None] = mapped_column(String(100), nullable=True)
    lot_id: Mapped[int | None] = mapped_column(ForeignKey("lots.id"), nullable=True)
    mesure_id: Mapped[int | None] = mapped_column(ForeignKey("mesures.id"), nullable=True)
    statut: Mapped[str] = mapped_column(String(20), nullable=False, default="ouverte")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("ix_alertes_pays", "pays"),
        Index("ix_alertes_statut", "statut"),
        Index("ix_alertes_type", "type_alerte"),
    )
