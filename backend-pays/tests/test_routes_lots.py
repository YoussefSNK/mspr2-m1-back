"""
TDD — Tests des routes API /api/lots (via TestClient + SQLite en mémoire).
"""
import pytest
from datetime import datetime, timezone, timedelta


class TestGetLots:
    def test_liste_vide_au_depart(self, client):
        response = client.get("/api/lots")
        assert response.status_code == 200
        assert response.json() == []

    def test_liste_retourne_lots_crees(self, client, lot_bresil_payload):
        client.post("/api/lots", json=lot_bresil_payload)
        response = client.get("/api/lots")
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_lots_tries_par_date_stockage(self, client):
        payload1 = {
            "lot_code": "LOT-001",
            "pays": "bresil",
            "exploitation": "Fazenda",
            "entrepot": "e1",
            "date_stockage": "2024-01-01T00:00:00Z",
        }
        payload2 = {
            "lot_code": "LOT-002",
            "pays": "bresil",
            "exploitation": "Fazenda",
            "entrepot": "e1",
            "date_stockage": "2023-01-01T00:00:00Z",
        }
        client.post("/api/lots", json=payload1)
        client.post("/api/lots", json=payload2)
        response = client.get("/api/lots")
        lots = response.json()
        assert lots[0]["lot_code"] == "LOT-002"
        assert lots[1]["lot_code"] == "LOT-001"


class TestPostLot:
    def test_creer_lot_retourne_201(self, client, lot_bresil_payload):
        response = client.post("/api/lots", json=lot_bresil_payload)
        assert response.status_code == 201

    def test_creer_lot_retourne_les_donnees(self, client, lot_bresil_payload):
        response = client.post("/api/lots", json=lot_bresil_payload)
        data = response.json()
        assert data["lot_code"] == "LOT-BR-001"
        assert data["pays"] == "bresil"
        assert data["statut"] == "conforme"
        assert "id" in data

    def test_doublon_lot_code_retourne_409(self, client, lot_bresil_payload):
        client.post("/api/lots", json=lot_bresil_payload)
        response = client.post("/api/lots", json=lot_bresil_payload)
        assert response.status_code == 409

    def test_pays_invalide_retourne_422(self, client, lot_bresil_payload):
        lot_bresil_payload["pays"] = "france"
        response = client.post("/api/lots", json=lot_bresil_payload)
        assert response.status_code == 422

    def test_champ_manquant_retourne_422(self, client):
        response = client.post("/api/lots", json={"lot_code": "LOT-001"})
        assert response.status_code == 422


class TestGetLotById:
    def test_lot_existant_retourne_200(self, client, lot_bresil_payload):
        created = client.post("/api/lots", json=lot_bresil_payload).json()
        response = client.get(f"/api/lots/{created['id']}")
        assert response.status_code == 200
        assert response.json()["lot_code"] == "LOT-BR-001"

    def test_lot_inexistant_retourne_404(self, client):
        response = client.get("/api/lots/9999")
        assert response.status_code == 404


class TestPutLot:
    def test_mise_a_jour_statut(self, client, lot_bresil_payload):
        created = client.post("/api/lots", json=lot_bresil_payload).json()
        response = client.put(f"/api/lots/{created['id']}", json={"statut": "expedie"})
        assert response.status_code == 200
        assert response.json()["statut"] == "expedie"

    def test_mise_a_jour_lot_inexistant_404(self, client):
        response = client.put("/api/lots/9999", json={"statut": "expedie"})
        assert response.status_code == 404


class TestDeleteLot:
    def test_supprimer_lot_retourne_204(self, client, lot_bresil_payload):
        created = client.post("/api/lots", json=lot_bresil_payload).json()
        response = client.delete(f"/api/lots/{created['id']}")
        assert response.status_code == 204

    def test_apres_suppression_lot_introuvable(self, client, lot_bresil_payload):
        created = client.post("/api/lots", json=lot_bresil_payload).json()
        client.delete(f"/api/lots/{created['id']}")
        response = client.get(f"/api/lots/{created['id']}")
        assert response.status_code == 404

    def test_supprimer_lot_inexistant_404(self, client):
        response = client.delete("/api/lots/9999")
        assert response.status_code == 404


class TestFifoLots:
    def test_fifo_exclut_lots_expires_et_expedies(self, client):
        payloads = [
            {
                "lot_code": "LOT-CONFORME",
                "pays": "bresil",
                "exploitation": "F",
                "entrepot": "e1",
                "date_stockage": "2025-01-01T00:00:00Z",
                "statut": "conforme",
            },
            {
                "lot_code": "LOT-EXPEDIE",
                "pays": "bresil",
                "exploitation": "F",
                "entrepot": "e1",
                "date_stockage": "2024-01-01T00:00:00Z",
                "statut": "expedie",
            },
            {
                "lot_code": "LOT-PERIME",
                "pays": "bresil",
                "exploitation": "F",
                "entrepot": "e1",
                "date_stockage": "2023-01-01T00:00:00Z",
                "statut": "perime",
            },
        ]
        for p in payloads:
            client.post("/api/lots", json=p)

        response = client.get("/api/lots/fifo")
        assert response.status_code == 200
        lots = response.json()
        codes = [l["lot_code"] for l in lots]
        assert "LOT-CONFORME" in codes
        assert "LOT-EXPEDIE" not in codes
        assert "LOT-PERIME" not in codes
