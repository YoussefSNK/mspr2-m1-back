from datetime import datetime
from pydantic import BaseModel, field_validator
from typing import Literal

StatutLot = Literal["conforme", "en_alerte", "perime", "expedie"]


class LotCreate(BaseModel):
    lot_code: str
    pays: str
    exploitation: str
    entrepot: str
    date_stockage: datetime
    statut: StatutLot = "conforme"

    @field_validator("pays")
    @classmethod
    def pays_valide(cls, v: str) -> str:
        pays_autorises = {"bresil", "equateur", "colombie"}
        if v.lower() not in pays_autorises:
            raise ValueError(f"Pays doit être parmi {pays_autorises}")
        return v.lower()


class LotUpdate(BaseModel):
    exploitation: str | None = None
    entrepot: str | None = None
    statut: StatutLot | None = None


class LotRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    lot_code: str
    pays: str
    exploitation: str
    entrepot: str
    date_stockage: datetime
    statut: str
    created_at: datetime
    updated_at: datetime
