"""
Tests de routes complémentaires : endpoints non couverts par
test_central_routes.py (mesures consolidées, stocks en erreur,
routes par pays pour alertes et mesures).
"""
import respx
import httpx


BRESIL_URL = "http://backend-bresil:8000"
EQUATEUR_URL = "http://backend-equateur:8000"
COLOMBIE_URL = "http://backend-colombie:8000"

MESURES_BRESIL = [
    {"id": 1, "temperature": 28.4, "humidite": 55.2, "pays": "bresil",
     "entrepot": "e1", "lot_id": 1, "statut": "OK",
     "date_mesure": "2026-06-16T10:00:00Z"}
]


class TestCentralMesures:
    @respx.mock
    def test_get_mesures_consolide(self, client):
        respx.get(f"{BRESIL_URL}/api/mesures").mock(
            return_value=httpx.Response(200, json=MESURES_BRESIL)
        )
        respx.get(f"{EQUATEUR_URL}/api/mesures").mock(
            return_value=httpx.Response(200, json=[])
        )
        respx.get(f"{COLOMBIE_URL}/api/mesures").mock(
            return_value=httpx.Response(200, json=[])
        )

        response = client.get("/central/mesures")
        assert response.status_code == 200
        assert response.json()["total"] == 1

    @respx.mock
    def test_get_mesures_par_pays(self, client):
        respx.get(f"{COLOMBIE_URL}/api/mesures").mock(
            return_value=httpx.Response(200, json=MESURES_BRESIL)
        )

        response = client.get("/central/pays/colombie/mesures")
        assert response.status_code == 200
        data = response.json()
        assert data["pays"] == "colombie"
        assert len(data["data"]) == 1

    @respx.mock
    def test_get_mesures_par_pays_indisponible(self, client):
        respx.get(f"{COLOMBIE_URL}/api/mesures").mock(
            side_effect=httpx.ConnectError("refused")
        )

        response = client.get("/central/pays/colombie/mesures")
        assert response.status_code == 200
        data = response.json()
        assert "error" in data
        assert data["data"] == []


class TestCentralAlertesParPays:
    @respx.mock
    def test_get_alertes_par_pays(self, client):
        alertes = [
            {"id": 1, "type_alerte": "lot_trop_ancien", "message": "vieux",
             "niveau": "critical", "pays": "equateur", "entrepot": "e2",
             "lot_id": 5, "mesure_id": None, "statut": "ouverte",
             "created_at": "2026-06-16T10:00:00Z"}
        ]
        respx.get(f"{EQUATEUR_URL}/api/alertes").mock(
            return_value=httpx.Response(200, json=alertes)
        )

        response = client.get("/central/pays/equateur/alertes")
        assert response.status_code == 200
        data = response.json()
        assert data["pays"] == "equateur"
        assert len(data["data"]) == 1

    @respx.mock
    def test_get_alertes_par_pays_indisponible(self, client):
        respx.get(f"{EQUATEUR_URL}/api/alertes").mock(
            side_effect=httpx.ConnectError("refused")
        )

        response = client.get("/central/pays/equateur/alertes")
        assert response.status_code == 200
        data = response.json()
        assert "error" in data
        assert data["data"] == []


class TestCentralPaysInconnu:
    def test_lots_pays_inconnu_retourne_erreur(self, client):
        response = client.get("/central/pays/japon/lots")
        assert response.status_code == 200
        data = response.json()
        assert "error" in data
        assert "inconnu" in data["error"].lower()
        assert data["data"] == []


class TestCentralStocksDegrade:
    @respx.mock
    def test_stocks_avec_backend_indisponible(self, client):
        respx.get(f"{BRESIL_URL}/api/lots/fifo").mock(
            return_value=httpx.Response(200, json=[{"id": 1, "lot_code": "LOT-BR-001"}])
        )
        respx.get(f"{EQUATEUR_URL}/api/lots/fifo").mock(
            side_effect=httpx.ConnectError("refused")
        )
        respx.get(f"{COLOMBIE_URL}/api/lots/fifo").mock(
            return_value=httpx.Response(200, json=[])
        )

        response = client.get("/central/stocks")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert "equateur" in data["errors"]
