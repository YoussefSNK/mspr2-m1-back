from datetime import datetime
from pydantic import BaseModel
from typing import Literal

NiveauAlerte = Literal["info", "warning", "critique"]
StatutAlerte = Literal["ouverte", "traitee", "ignoree"]
TypeAlerte = Literal["temperature_hors_seuil", "humidite_hors_seuil", "lot_trop_ancien"]


class AlerteRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    type_alerte: str
    message: str
    niveau: str
    pays: str
    entrepot: str | None
    lot_id: int | None
    mesure_id: int | None
    statut: str
    created_at: datetime


class AlerteResoudre(BaseModel):
    statut: StatutAlerte
