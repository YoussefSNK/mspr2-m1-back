import logging
from sqlalchemy.orm import Session

from app.models.alerte import Alerte
from app.models.lot import Lot
from app.services.alert_rules import ViolationSeuil, verifier_mesure, verifier_lot_ancien
from app.services.email_service import send_alert_email

logger = logging.getLogger(__name__)


def creer_alerte(
    db: Session,
    violation: ViolationSeuil,
    pays: str,
    entrepot: str,
    lot_id: int | None = None,
    mesure_id: int | None = None,
) -> Alerte:
    alerte = Alerte(
        type_alerte=violation.type_alerte,
        message=violation.message,
        niveau=violation.niveau,
        pays=pays,
        entrepot=entrepot,
        lot_id=lot_id,
        mesure_id=mesure_id,
        statut="ouverte",
    )
    db.add(alerte)
    db.commit()
    db.refresh(alerte)
    logger.info("Alerte créée : %s | pays=%s | entrepot=%s", violation.type_alerte, pays, entrepot)

    send_alert_email(pays, entrepot, violation.type_alerte, violation.message)
    return alerte


def traiter_mesure_alertes(
    db: Session,
    pays: str,
    entrepot: str,
    temperature: float,
    humidite: float,
    mesure_id: int,
) -> list[Alerte]:
    violations = verifier_mesure(pays, temperature, humidite)
    alertes = []
    for v in violations:
        a = creer_alerte(db, v, pays, entrepot, mesure_id=mesure_id)
        alertes.append(a)
    return alertes


def verifier_lots_anciens(db: Session) -> list[Alerte]:
    lots_actifs = db.query(Lot).filter(Lot.statut.in_(["conforme", "en_alerte"])).all()
    alertes = []
    for lot in lots_actifs:
        violation = verifier_lot_ancien(lot.date_stockage, lot.lot_code, lot.pays)
        if violation:
            lot.statut = "perime"
            db.commit()
            a = creer_alerte(
                db,
                violation,
                lot.pays,
                lot.entrepot,
                lot_id=lot.id,
            )
            alertes.append(a)
    return alertes
