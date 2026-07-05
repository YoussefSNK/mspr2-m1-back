"""
TDD — Tests d'intégration du flux MQTT (simulé sans broker réel).
Format réel Raspberry Pi :
  Topic   : futurkawa/entrepot/bresil
  Payload : {"timestamp": 1718615743, "temperature": 28.4, "humidity": 55.2, "status": "OK"}
"""
import json
from unittest.mock import patch, MagicMock

from app.services.mqtt_service import _on_message, _parse_topic
from app.models.mesure import Mesure
from app.models.alerte import Alerte

# Topic réel du Raspberry Pi
TOPIC_BRESIL = "futurkawa/entrepot/bresil"

# Payload réel du Raspberry Pi
PAYLOAD_NORMAL = {
    "timestamp": 1718615743,
    "temperature": 28.4,
    "humidity": 55.2,
    "status": "OK",
}

PAYLOAD_HORS_SEUIL = {
    "timestamp": 1718615743,
    "temperature": 40.0,
    "humidity": 70.0,
    "status": "OK",
}


def make_mqtt_message(payload: dict, topic: str = TOPIC_BRESIL) -> MagicMock:
    msg = MagicMock()
    msg.topic = topic
    msg.payload = json.dumps(payload).encode("utf-8")
    return msg


class TestParseTopic:
    def test_topic_bresil_extrait_entrepot_et_pays(self):
        result = _parse_topic("futurkawa/entrepot/bresil")
        assert result == ("entrepot", "bresil")

    def test_topic_equateur(self):
        result = _parse_topic("futurkawa/entrepot/equateur")
        assert result == ("entrepot", "equateur")

    def test_topic_colombie(self):
        result = _parse_topic("futurkawa/entrepot/colombie")
        assert result == ("entrepot", "colombie")

    def test_topic_trop_court_retourne_none(self):
        assert _parse_topic("futurkawa/bresil") is None

    def test_topic_trop_long_retourne_none(self):
        assert _parse_topic("futurkawa/entrepot/bresil/extra") is None

    def test_topic_vide_retourne_none(self):
        assert _parse_topic("") is None


class TestMqttOnMessage:
    def test_payload_valide_persiste_mesure(self, db):
        msg = make_mqtt_message(PAYLOAD_NORMAL)
        with patch("app.services.mqtt_service.SessionLocal", return_value=db):
            with patch("app.services.email_service.send_alert_email", return_value=False):
                _on_message(None, None, msg)

        mesures = db.query(Mesure).all()
        assert len(mesures) == 1
        assert mesures[0].temperature == 28.4
        assert mesures[0].humidite == 55.2
        assert mesures[0].pays == "bresil"
        assert mesures[0].entrepot == "entrepot"

    def test_timestamp_unix_converti_en_datetime(self, db):
        msg = make_mqtt_message(PAYLOAD_NORMAL)
        with patch("app.services.mqtt_service.SessionLocal", return_value=db):
            with patch("app.services.email_service.send_alert_email", return_value=False):
                _on_message(None, None, msg)

        mesure = db.query(Mesure).first()
        assert mesure.date_mesure is not None
        # 1718615743 = 2024-06-17 (environ)
        assert mesure.date_mesure.year == 2024

    def test_payload_hors_seuil_cree_alerte(self, db):
        msg = make_mqtt_message(PAYLOAD_HORS_SEUIL)
        with patch("app.services.mqtt_service.SessionLocal", return_value=db):
            with patch("app.services.email_service.send_alert_email", return_value=False):
                _on_message(None, None, msg)

        alertes = db.query(Alerte).all()
        assert len(alertes) >= 1

    def test_payload_normal_ne_cree_pas_dalerte(self, db):
        msg = make_mqtt_message(PAYLOAD_NORMAL)
        with patch("app.services.mqtt_service.SessionLocal", return_value=db):
            with patch("app.services.email_service.send_alert_email", return_value=False):
                _on_message(None, None, msg)

        alertes = db.query(Alerte).all()
        assert len(alertes) == 0

    def test_payload_json_invalide_ne_plante_pas(self, db):
        msg = MagicMock()
        msg.topic = TOPIC_BRESIL
        msg.payload = b"invalid json {"
        with patch("app.services.mqtt_service.SessionLocal", return_value=db):
            _on_message(None, None, msg)

        assert db.query(Mesure).count() == 0

    def test_payload_champs_manquants_ne_plante_pas(self, db):
        # Manque humidity et status
        msg = make_mqtt_message({"timestamp": 1718615743, "temperature": 28.4})
        with patch("app.services.mqtt_service.SessionLocal", return_value=db):
            _on_message(None, None, msg)

        assert db.query(Mesure).count() == 0

    def test_topic_invalide_ne_plante_pas(self, db):
        msg = MagicMock()
        msg.topic = "mauvais/topic"
        msg.payload = json.dumps(PAYLOAD_NORMAL).encode("utf-8")
        with patch("app.services.mqtt_service.SessionLocal", return_value=db):
            _on_message(None, None, msg)

        assert db.query(Mesure).count() == 0

    def test_equateur_utilise_ses_propres_seuils(self, db):
        payload_eq_ok = {
            "timestamp": 1718615743,
            "temperature": 31.0,
            "humidity": 60.0,
            "status": "OK",
        }
        msg = make_mqtt_message(payload_eq_ok, topic="futurkawa/entrepot/equateur")
        with patch("app.services.mqtt_service.SessionLocal", return_value=db):
            with patch("app.services.email_service.send_alert_email", return_value=False):
                _on_message(None, None, msg)

        assert db.query(Alerte).count() == 0
