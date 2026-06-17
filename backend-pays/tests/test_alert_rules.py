"""
TDD — Tests des règles métier pures (sans DB, sans I/O).
Ces tests définissent le comportement attendu AVANT l'implémentation.
"""
import pytest
from datetime import datetime, timezone, timedelta

from app.services.alert_rules import (
    verifier_temperature,
    verifier_humidite,
    verifier_lot_ancien,
    verifier_mesure,
    ViolationSeuil,
)


class TestVerifierTemperature:
    def test_temperature_ideale_bresil_pas_dalerte(self):
        assert verifier_temperature("bresil", 29.0) is None

    def test_temperature_dans_tolerance_basse_bresil(self):
        assert verifier_temperature("bresil", 26.0) is None  # 29 - 3 = 26

    def test_temperature_dans_tolerance_haute_bresil(self):
        assert verifier_temperature("bresil", 32.0) is None  # 29 + 3 = 32

    def test_temperature_hors_seuil_haute_bresil(self):
        result = verifier_temperature("bresil", 33.0)
        assert result is not None
        assert result.type_alerte == "temperature_hors_seuil"
        assert result.valeur == 33.0
        assert result.seuil_ideal == 29.0

    def test_temperature_hors_seuil_basse_bresil(self):
        result = verifier_temperature("bresil", 25.0)
        assert result is not None
        assert result.type_alerte == "temperature_hors_seuil"

    def test_temperature_ideale_equateur(self):
        assert verifier_temperature("equateur", 31.0) is None

    def test_temperature_hors_seuil_equateur(self):
        result = verifier_temperature("equateur", 35.0)
        assert result is not None

    def test_temperature_ideale_colombie(self):
        assert verifier_temperature("colombie", 26.0) is None

    def test_temperature_critique_si_ecart_double(self):
        result = verifier_temperature("bresil", 35.5)  # écart = 6.5 > 3*2 = 6
        assert result is not None
        assert result.niveau == "critique"

    def test_temperature_warning_si_ecart_simple(self):
        result = verifier_temperature("bresil", 33.0)  # écart = 4 < 6
        assert result is not None
        assert result.niveau == "warning"

    def test_pays_inconnu_leve_exception(self):
        with pytest.raises(ValueError, match="Pays inconnu"):
            verifier_temperature("france", 20.0)

    def test_retourne_violation_seuil_dataclass(self):
        result = verifier_temperature("bresil", 35.0)
        assert isinstance(result, ViolationSeuil)

    def test_limite_exacte_basse_est_ok(self):
        assert verifier_temperature("bresil", 26.0) is None

    def test_un_dixieme_sous_limite_basse_est_alerte(self):
        result = verifier_temperature("bresil", 25.9)
        assert result is not None


class TestVerifierHumidite:
    def test_humidite_ideale_bresil_pas_dalerte(self):
        assert verifier_humidite("bresil", 55.0) is None

    def test_humidite_dans_tolerance_basse(self):
        assert verifier_humidite("bresil", 53.0) is None  # 55 - 2

    def test_humidite_dans_tolerance_haute(self):
        assert verifier_humidite("bresil", 57.0) is None  # 55 + 2

    def test_humidite_hors_seuil_haute(self):
        result = verifier_humidite("bresil", 58.0)
        assert result is not None
        assert result.type_alerte == "humidite_hors_seuil"

    def test_humidite_hors_seuil_basse(self):
        result = verifier_humidite("bresil", 52.0)
        assert result is not None

    def test_humidite_ideale_colombie(self):
        assert verifier_humidite("colombie", 80.0) is None

    def test_humidite_hors_seuil_colombie(self):
        result = verifier_humidite("colombie", 75.0)
        assert result is not None

    def test_pays_inconnu_leve_exception(self):
        with pytest.raises(ValueError):
            verifier_humidite("japon", 50.0)


class TestVerifierLotAncien:
    def test_lot_recent_pas_dalerte(self):
        date_recente = datetime.now(timezone.utc) - timedelta(days=100)
        result = verifier_lot_ancien(date_recente, "LOT-001", "bresil")
        assert result is None

    def test_lot_exactement_365_jours_pas_dalerte(self):
        date = datetime.now(timezone.utc) - timedelta(days=365)
        result = verifier_lot_ancien(date, "LOT-001", "bresil")
        assert result is None

    def test_lot_366_jours_alerte(self):
        date = datetime.now(timezone.utc) - timedelta(days=366)
        result = verifier_lot_ancien(date, "LOT-001", "bresil")
        assert result is not None
        assert result.type_alerte == "lot_trop_ancien"

    def test_lot_400_jours_alerte_critique(self):
        date = datetime.now(timezone.utc) - timedelta(days=400)
        result = verifier_lot_ancien(date, "LOT-001", "bresil")
        assert result is not None
        assert result.niveau == "critique"

    def test_message_contient_lot_code(self):
        date = datetime.now(timezone.utc) - timedelta(days=400)
        result = verifier_lot_ancien(date, "LOT-BR-999", "bresil")
        assert result is not None
        assert "LOT-BR-999" in result.message

    def test_date_sans_timezone_fonctionne(self):
        date_naive = datetime.now() - timedelta(days=400)
        result = verifier_lot_ancien(date_naive, "LOT-001", "bresil")
        assert result is not None


class TestVerifierMesure:
    def test_mesure_normale_aucune_violation(self):
        violations = verifier_mesure("bresil", 29.0, 55.0)
        assert violations == []

    def test_mesure_temp_hors_seuil_une_violation(self):
        violations = verifier_mesure("bresil", 35.0, 55.0)
        assert len(violations) == 1
        assert violations[0].type_alerte == "temperature_hors_seuil"

    def test_mesure_hum_hors_seuil_une_violation(self):
        violations = verifier_mesure("bresil", 29.0, 60.0)
        assert len(violations) == 1
        assert violations[0].type_alerte == "humidite_hors_seuil"

    def test_mesure_tout_hors_seuil_deux_violations(self):
        violations = verifier_mesure("bresil", 35.0, 60.0)
        assert len(violations) == 2

    def test_mesure_equateur_utilise_ses_propres_seuils(self):
        violations = verifier_mesure("equateur", 31.0, 60.0)
        assert violations == []

    def test_mesure_colombie_utilise_ses_propres_seuils(self):
        violations = verifier_mesure("colombie", 26.0, 80.0)
        assert violations == []
