from datetime import datetime, timezone
from pydantic import BaseModel, field_validator


class MesureCreate(BaseModel):
    pays: str
    entrepot: str
    temperature: float
    humidite: float
    statut: str = "ok"
    date_mesure: datetime
    lot_id: int | None = None

    @field_validator("pays")
    @classmethod
    def pays_valide(cls, v: str) -> str:
        pays_autorises = {"bresil", "equateur", "colombie"}
        if v.lower() not in pays_autorises:
            raise ValueError(f"Pays doit être parmi {pays_autorises}")
        return v.lower()

    @field_validator("temperature")
    @classmethod
    def temperature_range(cls, v: float) -> float:
        if not (-50 <= v <= 100):
            raise ValueError("Température hors plage physique [-50, 100]°C")
        return v

    @field_validator("humidite")
    @classmethod
    def humidite_range(cls, v: float) -> float:
        if not (0 <= v <= 100):
            raise ValueError("Humidité doit être entre 0 et 100 %")
        return v


class MesureRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    pays: str
    entrepot: str
    temperature: float
    humidite: float
    statut: str
    date_mesure: datetime
    lot_id: int | None
    created_at: datetime


class MesureIoT(BaseModel):
    """
    Payload reçu depuis le Raspberry Pi via MQTT.
    Topic : futurkawa/entrepot/{pays}
    Champs exacts du capteur : timestamp (Unix int), temperature, humidity, status.
    """
    timestamp: int
    temperature: float
    humidity: float
    status: str = "OK"

    def to_mesure_data(self, pays: str, entrepot: str) -> dict:
        """Convertit le payload IoT vers les champs internes (snake_case FR)."""
        return {
            "pays": pays,
            "entrepot": entrepot,
            "temperature": self.temperature,
            "humidite": self.humidity,
            "statut": self.status.lower(),
            "date_mesure": datetime.fromtimestamp(self.timestamp, tz=timezone.utc),
        }
