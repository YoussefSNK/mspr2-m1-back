from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Identité du pays
    PAYS: str = "bresil"

    # Base de données
    DATABASE_URL: str = "postgresql://futurekawa:futurekawa@localhost:5432/futurekawa_bresil"

    # MQTT — Raspberry Pi (10.3.141.1 ou 172.20.10.11 en fallback)
    MQTT_BROKER_HOST: str = "10.3.141.1"
    MQTT_BROKER_PORT: int = 1883
    # Préfixe tel que défini par le Raspberry Pi : "futurkawa" (sans 'e')
    MQTT_TOPIC_PREFIX: str = "futurkawa"

    # Email
    SMTP_HOST: str = "smtp.example.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@futurekawa.com"

    EMAIL_RESPONSABLE_BRESIL: str = "responsable.bresil@futurekawa.com"
    EMAIL_RESPONSABLE_EQUATEUR: str = "responsable.equateur@futurekawa.com"
    EMAIL_RESPONSABLE_COLOMBIE: str = "responsable.colombie@futurekawa.com"

    # CORS
    CORS_ORIGINS: list[str] = ["*"]

    # Scheduler — vérification périodique des lots trop anciens
    SCHEDULER_ENABLED: bool = True
    # Intervalle entre deux vérifications, en secondes (défaut : 24 h).
    # La péremption est un seuil en jours (> 365 j) : une vérification
    # quotidienne suffit, inutile de requêter plus souvent.
    SCHEDULER_INTERVAL_SECONDS: int = 24 * 60 * 60


SEUILS_PAYS: dict[str, dict[str, float]] = {
    "bresil": {"temperature": 29.0, "humidite": 55.0},
    "equateur": {"temperature": 31.0, "humidite": 60.0},
    "colombie": {"temperature": 26.0, "humidite": 80.0},
}

TOLERANCE_TEMP: float = 3.0
TOLERANCE_HUMIDITE: float = 2.0

LOT_MAX_JOURS: int = 365


def get_settings() -> Settings:
    return Settings()
