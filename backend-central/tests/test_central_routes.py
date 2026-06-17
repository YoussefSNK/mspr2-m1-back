"""
TDD — Tests du backend central siège.
On mocke les backends pays via respx (mock httpx).
"""
import pytest
import respx
import httpx
from unittest.mock import patch


LOTS_BRESIL = [
    {"id": 1, "lot_code": "LOT-BR-001", "pays": "bresil", "statut": "conforme",
     "exploitation": "Fazenda", "entrepot": "e1", "date_stockage": "2025-01-01T00:00:00Z",
     "created_at": "2025-01-01T00:00:00Z", "updated_at": "2025-01-01T00:00:00Z"}
]
LOTS_EQUATEUR = [
    {"id": 2, "lot_code": "LOT-EQ-001", "pays": "equateur", "statut": "conforme",
     "exploitation": "Hacienda", "entrepot": "e2", "date_stockage": "2025-02-01T00:00:00Z",
     "created_at": "2025-02-01T00:00:00Z", "updated_at": "2025-02-01T00:00:00Z"}
]


class TestCentralHealth:
    def test_health_retourne_ok(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert response.json()["role"] == "central"


class TestCentralLots:
    @respx.mock
    def test_get_lots_consolide_tous_pays(self, client):
        respx.get("http://backend-bresil:8000/api/lots").mock(
            return_value=httpx.Response(200, json=LOTS_BRESIL)
        )
        respx.get("http://backend-equateur:8000/api/lots").mock(
            return_value=httpx.Response(200, json=LOTS_EQUATEUR)
        )
        respx.get("http://backend-colombie:8000/api/lots").mock(
            return_value=httpx.Response(200, json=[])
        )

        response = client.get("/central/lots")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["data"]) == 2

    @respx.mock
    def test_get_lots_backend_indisponible_retour_partiel(self, client):
        respx.get("http://backend-bresil:8000/api/lots").mock(
            return_value=httpx.Response(200, json=LOTS_BRESIL)
        )
        respx.get("http://backend-equateur:8000/api/lots").mock(
            side_effect=httpx.ConnectError("refused")
        )
        respx.get("http://backend-colombie:8000/api/lots").mock(
            side_effect=httpx.ConnectError("refused")
        )

        response = client.get("/central/lots")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert "equateur" in data["errors"]

    @respx.mock
    def test_get_lots_par_pays_bresil(self, client):
        respx.get("http://backend-bresil:8000/api/lots").mock(
            return_value=httpx.Response(200, json=LOTS_BRESIL)
        )

        response = client.get("/central/pays/bresil/lots")
        assert response.status_code == 200
        data = response.json()
        assert data["pays"] == "bresil"
        assert len(data["data"]) == 1

    @respx.mock
    def test_get_lots_par_pays_indisponible_retourne_erreur(self, client):
        respx.get("http://backend-bresil:8000/api/lots").mock(
            side_effect=httpx.ConnectError("refused")
        )

        response = client.get("/central/pays/bresil/lots")
        assert response.status_code == 200
        data = response.json()
        assert "error" in data
        assert data["data"] == []


class TestCentralAlertes:
    @respx.mock
    def test_get_alertes_consolide(self, client):
        alertes = [
            {"id": 1, "type_alerte": "temperature_hors_seuil", "message": "test",
             "niveau": "warning", "pays": "bresil", "entrepot": "e1",
             "lot_id": None, "mesure_id": 1, "statut": "ouverte",
             "created_at": "2026-06-16T10:00:00Z"}
        ]
        respx.get("http://backend-bresil:8000/api/alertes").mock(
            return_value=httpx.Response(200, json=alertes)
        )
        respx.get("http://backend-equateur:8000/api/alertes").mock(
            return_value=httpx.Response(200, json=[])
        )
        respx.get("http://backend-colombie:8000/api/alertes").mock(
            return_value=httpx.Response(200, json=[])
        )

        response = client.get("/central/alertes")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1


class TestCentralStocks:
    @respx.mock
    def test_stocks_utilise_endpoint_fifo(self, client):
        respx.get("http://backend-bresil:8000/api/lots/fifo").mock(
            return_value=httpx.Response(200, json=LOTS_BRESIL)
        )
        respx.get("http://backend-equateur:8000/api/lots/fifo").mock(
            return_value=httpx.Response(200, json=[])
        )
        respx.get("http://backend-colombie:8000/api/lots/fifo").mock(
            return_value=httpx.Response(200, json=[])
        )

        response = client.get("/central/stocks")
        assert response.status_code == 200
        assert response.json()["total"] == 1
