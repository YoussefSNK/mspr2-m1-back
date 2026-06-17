"""
Fixtures partagées pour tous les tests.
Utilise SQLite sur un fichier temporaire unique par test pour que
toutes les connexions voient les mêmes tables et données.
"""
import pytest
import tempfile
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.database import Base, get_db
from app.main import app


@asynccontextmanager
async def lifespan_test(fastapi_app):
    """Lifespan neutre : pas de connexion PostgreSQL ni MQTT pendant les tests."""
    yield


@pytest.fixture(scope="function")
def db():
    # Fichier temporaire — toutes les connexions voient les mêmes tables
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)
    url = f"sqlite:///{db_path}"

    engine = create_engine(url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()
        engine.dispose()
        os.unlink(db_path)


@pytest.fixture(scope="function")
def client(db: Session):
    def override_get_db():
        yield db

    app.router.lifespan_context = lifespan_test
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app, raise_server_exceptions=True) as c:
        yield c

    app.dependency_overrides.clear()


# ── Payloads de test ──────────────────────────────────────────────────────────

@pytest.fixture
def lot_bresil_payload() -> dict:
    return {
        "lot_code": "LOT-BR-001",
        "pays": "bresil",
        "exploitation": "Fazenda Norte",
        "entrepot": "entrepot-1",
        "date_stockage": "2025-01-15T08:00:00Z",
        "statut": "conforme",
    }


@pytest.fixture
def lot_ancien_payload() -> dict:
    """Lot stocké il y a plus de 365 jours."""
    date_ancienne = (datetime.now(timezone.utc) - timedelta(days=400)).isoformat()
    return {
        "lot_code": "LOT-BR-ANCIEN",
        "pays": "bresil",
        "exploitation": "Fazenda Norte",
        "entrepot": "entrepot-1",
        "date_stockage": date_ancienne,
        "statut": "conforme",
    }


@pytest.fixture
def mesure_normale_bresil() -> dict:
    return {
        "pays": "bresil",
        "entrepot": "entrepot-1",
        "temperature": 29.0,
        "humidite": 55.0,
        "statut": "ok",
        "date_mesure": "2026-06-16T10:00:00Z",
    }


@pytest.fixture
def mesure_hors_seuil_bresil() -> dict:
    return {
        "pays": "bresil",
        "entrepot": "entrepot-1",
        "temperature": 35.0,
        "humidite": 65.0,
        "statut": "ok",
        "date_mesure": "2026-06-16T10:00:00Z",
    }
