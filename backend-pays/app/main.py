import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import engine
from app.models import Lot, Mesure, Alerte  # noqa: F401 — force table registration
from app.core.database import Base
from app.routes import lots, mesures, alertes, lots_mesures

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

_mqtt_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    logger.info("Tables SQL créées/vérifiées")

    global _mqtt_client
    try:
        from app.services.mqtt_service import start_mqtt_client
        _mqtt_client = start_mqtt_client()
    except Exception as exc:
        logger.warning("MQTT non démarré (mode dégradé) : %s", exc)

    yield

    if _mqtt_client:
        _mqtt_client.loop_stop()
        _mqtt_client.disconnect()
        logger.info("Client MQTT arrêté")


app = FastAPI(
    title=f"FutureKawa — Backend Pays ({settings.PAYS})",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(lots.router)
app.include_router(mesures.router)
app.include_router(alertes.router)
app.include_router(lots_mesures.router)


@app.get("/health")
def health():
    return {"status": "ok", "pays": settings.PAYS}
