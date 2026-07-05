"""
TDD — Tests des routes API /api/alertes.
"""
from unittest.mock import patch


class TestGetAlertes:
    def test_liste_vide_au_depart(self, client):
        response = client.get("/api/alertes")
        assert response.status_code == 200
        assert response.json() == []

    def test_alerte_creee_apres_mesure_hors_seuil(self, client, mesure_hors_seuil_bresil):
        with patch("app.services.email_service.send_alert_email", return_value=False):
            client.post("/api/mesures", json=mesure_hors_seuil_bresil)
        response = client.get("/api/alertes")
        assert response.status_code == 200
        assert len(response.json()) >= 1


class TestGetAlerteById:
    def test_alerte_inexistante_retourne_404(self, client):
        response = client.get("/api/alertes/9999")
        assert response.status_code == 404

    def test_alerte_existante_retourne_200(self, client, mesure_hors_seuil_bresil):
        with patch("app.services.email_service.send_alert_email", return_value=False):
            client.post("/api/mesures", json=mesure_hors_seuil_bresil)
        alertes = client.get("/api/alertes").json()
        alerte_id = alertes[0]["id"]
        response = client.get(f"/api/alertes/{alerte_id}")
        assert response.status_code == 200


class TestResoudreAlerte:
    def test_resoudre_alerte_change_statut(self, client, mesure_hors_seuil_bresil):
        with patch("app.services.email_service.send_alert_email", return_value=False):
            client.post("/api/mesures", json=mesure_hors_seuil_bresil)
        alertes = client.get("/api/alertes").json()
        alerte_id = alertes[0]["id"]

        response = client.put(
            f"/api/alertes/{alerte_id}/resoudre",
            json={"statut": "traitee"},
        )
        assert response.status_code == 200
        assert response.json()["statut"] == "traitee"

    def test_resoudre_alerte_inexistante_retourne_404(self, client):
        response = client.put("/api/alertes/9999/resoudre", json={"statut": "traitee"})
        assert response.status_code == 404

    def test_statut_invalide_retourne_422(self, client, mesure_hors_seuil_bresil):
        with patch("app.services.email_service.send_alert_email", return_value=False):
            client.post("/api/mesures", json=mesure_hors_seuil_bresil)
        alertes = client.get("/api/alertes").json()
        alerte_id = alertes[0]["id"]

        response = client.put(
            f"/api/alertes/{alerte_id}/resoudre",
            json={"statut": "statut_inventé"},
        )
        assert response.status_code == 422


class TestCheckLotsAnciens:
    def test_check_lots_anciens_sans_lots_retourne_liste_vide(self, client):
        response = client.post("/api/alertes/check-lots-anciens")
        assert response.status_code == 200
        assert response.json() == []

    def test_check_lots_anciens_cree_alerte_pour_lot_perime(self, client, lot_ancien_payload):
        with patch("app.services.email_service.send_alert_email", return_value=False):
            client.post("/api/lots", json=lot_ancien_payload)
            response = client.post("/api/alertes/check-lots-anciens")
        assert response.status_code == 200
        alertes = response.json()
        assert len(alertes) == 1
        assert alertes[0]["type_alerte"] == "lot_trop_ancien"

    def test_check_lots_anciens_met_a_jour_statut_lot(self, client, lot_ancien_payload):
        with patch("app.services.email_service.send_alert_email", return_value=False):
            created = client.post("/api/lots", json=lot_ancien_payload).json()
            client.post("/api/alertes/check-lots-anciens")
        lot = client.get(f"/api/lots/{created['id']}").json()
        assert lot["statut"] == "perime"
