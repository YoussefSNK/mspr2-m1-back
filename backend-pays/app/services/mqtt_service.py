import json
import logging

import paho.mqtt.client as mqtt
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.mesure import Mesure
from app.schemas.mesure import MesureIoT
from app.services.alert_service import traiter_mesure_alertes
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)
settings = get_settings()


def _parse_topic(topic: str) -> tuple[str, str] | None:
    """
    Extrait (entrepot, pays) depuis le topic Raspberry Pi.
    Format attendu : futurkawa/entrepot/{pays}
    Exemple      : futurkawa/entrepot/bresil  -> ("entrepot", "bresil")
    """
    parts = topic.split("/")
    if len(parts) != 3:
        return None
    _, entrepot, pays = parts
    return entrepot, pays


def _on_connect(client: mqtt.Client, userdata: None, flags: dict, rc: int, properties=None) -> None:
    if rc == 0:
        # S'abonne au topic exact du Raspberry Pi + wildcard sur le pays
        topic = f"{settings.MQTT_TOPIC_PREFIX}/entrepot/+"
        client.subscribe(topic)
        logger.info("MQTT connecté, abonné à : %s", topic)
    else:
        logger.error("MQTT connexion échouée, code : %d", rc)


def _on_message(client: mqtt.Client, userdata: None, msg: mqtt.MQTTMessage) -> None:
    topic_info = _parse_topic(msg.topic)
    if topic_info is None:
        logger.error("Topic MQTT non reconnu : %s", msg.topic)
        return

    entrepot, pays = topic_info

    try:
        payload = json.loads(msg.payload.decode("utf-8"))
        mesure_iot = MesureIoT(**payload)
    except Exception as exc:
        logger.error("Payload MQTT invalide sur %s : %s", msg.topic, exc)
        return

    db: Session = SessionLocal()
    try:
        data = mesure_iot.to_mesure_data(pays=pays, entrepot=entrepot)
        mesure = Mesure(**data)
        db.add(mesure)
        db.commit()
        db.refresh(mesure)
        logger.info(
            "Mesure persistée id=%d | pays=%s | temp=%.1f | hum=%.1f",
            mesure.id, mesure.pays, mesure.temperature, mesure.humidite,
        )

        traiter_mesure_alertes(
            db,
            mesure.pays,
            mesure.entrepot,
            mesure.temperature,
            mesure.humidite,
            mesure.id,
        )
    except Exception as exc:
        db.rollback()
        logger.error("Erreur traitement mesure MQTT : %s", exc)
    finally:
        db.close()


def build_mqtt_client() -> mqtt.Client:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = _on_connect
    client.on_message = _on_message
    return client


def start_mqtt_client() -> mqtt.Client:
    client = build_mqtt_client()
    try:
        client.connect(settings.MQTT_BROKER_HOST, settings.MQTT_BROKER_PORT, keepalive=60)
        client.loop_start()
        logger.info(
            "Client MQTT démarré — broker %s:%d",
            settings.MQTT_BROKER_HOST,
            settings.MQTT_BROKER_PORT,
        )
    except Exception as exc:
        logger.error("Impossible de se connecter au broker MQTT : %s", exc)
    return client
