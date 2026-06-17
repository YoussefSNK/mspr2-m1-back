"""
Règles métier pures — sans dépendance DB ni I/O.
Toutes ces fonctions sont testées en TDD pur (pas de mock nécessaire).
"""
from datetime import datetime, timezone
from dataclasses import dataclass
from app.core.config import SEUILS_PAYS, TOLERANCE_TEMP, TOLERANCE_HUMIDITE, LOT_MAX_JOURS


@dataclass(frozen=True)
class ViolationSeuil:
    type_alerte: str
    message: str
    niveau: str
    valeur: float
    seuil_ideal: float
    tolerance: float


def verifier_temperature(pays: str, temperature: float) -> ViolationSeuil | None:
    seuils = SEUILS_PAYS.get(pays)
    if seuils is None:
        raise ValueError(f"Pays inconnu : {pays}")
    ideal = seuils["temperature"]
    if temperature < ideal - TOLERANCE_TEMP or temperature > ideal + TOLERANCE_TEMP:
        direction = "basse" if temperature < ideal else "haute"
        return ViolationSeuil(
            type_alerte="temperature_hors_seuil",
            message=(
                f"Température {direction} en {pays} : {temperature}°C "
                f"(idéal {ideal}°C ± {TOLERANCE_TEMP}°C)"
            ),
            niveau="critique" if abs(temperature - ideal) > TOLERANCE_TEMP * 2 else "warning",
            valeur=temperature,
            seuil_ideal=ideal,
            tolerance=TOLERANCE_TEMP,
        )
    return None


def verifier_humidite(pays: str, humidite: float) -> ViolationSeuil | None:
    seuils = SEUILS_PAYS.get(pays)
    if seuils is None:
        raise ValueError(f"Pays inconnu : {pays}")
    ideal = seuils["humidite"]
    if humidite < ideal - TOLERANCE_HUMIDITE or humidite > ideal + TOLERANCE_HUMIDITE:
        direction = "basse" if humidite < ideal else "haute"
        return ViolationSeuil(
            type_alerte="humidite_hors_seuil",
            message=(
                f"Humidité {direction} en {pays} : {humidite}% "
                f"(idéal {ideal}% ± {TOLERANCE_HUMIDITE}%)"
            ),
            niveau="critique" if abs(humidite - ideal) > TOLERANCE_HUMIDITE * 2 else "warning",
            valeur=humidite,
            seuil_ideal=ideal,
            tolerance=TOLERANCE_HUMIDITE,
        )
    return None


def verifier_lot_ancien(date_stockage: datetime, lot_code: str, pays: str) -> ViolationSeuil | None:
    now = datetime.now(timezone.utc)
    date_stockage_utc = date_stockage.replace(tzinfo=timezone.utc) if date_stockage.tzinfo is None else date_stockage
    jours = (now - date_stockage_utc).days
    if jours > LOT_MAX_JOURS:
        return ViolationSeuil(
            type_alerte="lot_trop_ancien",
            message=f"Lot {lot_code} en {pays} stocké depuis {jours} jours (max {LOT_MAX_JOURS}j)",
            niveau="critique",
            valeur=float(jours),
            seuil_ideal=float(LOT_MAX_JOURS),
            tolerance=0.0,
        )
    return None


def verifier_mesure(pays: str, temperature: float, humidite: float) -> list[ViolationSeuil]:
    violations: list[ViolationSeuil] = []
    v_temp = verifier_temperature(pays, temperature)
    if v_temp:
        violations.append(v_temp)
    v_hum = verifier_humidite(pays, humidite)
    if v_hum:
        violations.append(v_hum)
    return violations
