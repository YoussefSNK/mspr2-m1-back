"""
TDD — Tests des routes API /api/mesures.
"""
import pytest
from unittest.mock import patch


class TestPostMesure:
    def test_creer_mesure_retourne_201(self, client, mesure_normale_bresil):
        response = client.post("/api/mesures", json=mesure_normale_bresil)
        assert response.status_code == 201

    def test_mesure_creee_contient_les_champs(self, client, mesure_normale_bresil):
        response = client.post("/api/mesures", json=mesure_normale_bresil)
        data = response.json()
        assert data["pays"] == "bresil"
        assert data["temperature"] == 29.0
        assert data["humidite"] == 55.0
        assert "id" in data

    def test_temperature_hors_plage_physique_422(self, client):
        payload = {
            "pays": "bresil",
            "entrepot": "entrepot-1",
            "temperature": 200.0,
            "humidite": 55.0,
            "date_mesure": "2026-06-16T10:00:00Z",
        }
        response = client.post("/api/mesures", json=payload)
        assert response.status_code == 422

    def test_mesure_hors_seuil_cree_alerte(self, client, mesure_hors_seuil_bresil):
        with patch("app.services.email_service.send_alert_email", return_value=False):
            client.post("/api/mesures", json=mesure_hors_seuil_bresil)
            alertes = client.get("/api/alertes").json()
            assert len(alertes) > 0

    def test_mesure_normale_ne_cree_pas_dalerte(self, client, mesure_normale_bresil):
        client.post("/api/mesures", json=mesure_normale_bresil)
        alertes = client.get("/api/alertes").json()
        assert len(alertes) == 0


class TestGetMesures:
    def test_liste_vide_au_depart(self, client):
        response = client.get("/api/mesures")
        assert response.status_code == 200
        assert response.json() == []

    def test_filtre_par_pays(self, client, mesure_normale_bresil):
        client.post("/api/mesures", json=mesure_normale_bresil)
        response = client.get("/api/mesures?pays=bresil")
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_filtre_par_pays_inexistant_retourne_liste_vide(self, client, mesure_normale_bresil):
        client.post("/api/mesures", json=mesure_normale_bresil)
        response = client.get("/api/mesures?pays=colombie")
        assert response.json() == []

    def test_filtre_par_entrepot(self, client, mesure_normale_bresil):
        client.post("/api/mesures", json=mesure_normale_bresil)
        response = client.get("/api/mesures?entrepot=entrepot-1")
        assert len(response.json()) == 1

    def test_filtre_entrepot_inexistant_retourne_vide(self, client, mesure_normale_bresil):
        client.post("/api/mesures", json=mesure_normale_bresil)
        response = client.get("/api/mesures?entrepot=entrepot-99")
        assert response.json() == []
