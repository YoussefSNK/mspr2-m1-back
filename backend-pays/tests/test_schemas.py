"""
TDD — Validation des schémas Pydantic.
"""
import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from app.schemas.lot import LotCreate
from app.schemas.mesure import MesureCreate, MesureIoT


class TestLotCreateSchema:
    def test_lot_valide(self):
        lot = LotCreate(
            lot_code="LOT-001",
            pays="bresil",
            exploitation="Fazenda",
            entrepot="entrepot-1",
            date_stockage=datetime.now(timezone.utc),
        )
        assert lot.pays == "bresil"

    def test_pays_normalise_en_minuscule(self):
        lot = LotCreate(
            lot_code="LOT-001",
            pays="BRESIL",
            exploitation="Fazenda",
            entrepot="entrepot-1",
            date_stockage=datetime.now(timezone.utc),
        )
        assert lot.pays == "bresil"

    def test_pays_invalide_leve_validation_error(self):
        with pytest.raises(ValidationError):
            LotCreate(
                lot_code="LOT-001",
                pays="france",
                exploitation="Ferme",
                entrepot="entrepot-1",
                date_stockage=datetime.now(timezone.utc),
            )

    def test_statut_defaut_est_conforme(self):
        lot = LotCreate(
            lot_code="LOT-001",
            pays="colombie",
            exploitation="Finca",
            entrepot="entrepot-1",
            date_stockage=datetime.now(timezone.utc),
        )
        assert lot.statut == "conforme"

    def test_statut_invalide_leve_validation_error(self):
        with pytest.raises(ValidationError):
            LotCreate(
                lot_code="LOT-001",
                pays="bresil",
                exploitation="Fazenda",
                entrepot="entrepot-1",
                date_stockage=datetime.now(timezone.utc),
                statut="inconnu",
            )


class TestMesureCreateSchema:
    def test_mesure_valide(self):
        m = MesureCreate(
            pays="equateur",
            entrepot="entrepot-2",
            temperature=31.0,
            humidite=60.0,
            date_mesure=datetime.now(timezone.utc),
        )
        assert m.pays == "equateur"

    def test_temperature_hors_plage_physique(self):
        with pytest.raises(ValidationError):
            MesureCreate(
                pays="bresil",
                entrepot="e1",
                temperature=150.0,
                humidite=55.0,
                date_mesure=datetime.now(timezone.utc),
            )

    def test_humidite_negative_invalide(self):
        with pytest.raises(ValidationError):
            MesureCreate(
                pays="bresil",
                entrepot="e1",
                temperature=29.0,
                humidite=-5.0,
                date_mesure=datetime.now(timezone.utc),
            )

    def test_humidite_superieure_100_invalide(self):
        with pytest.raises(ValidationError):
            MesureCreate(
                pays="bresil",
                entrepot="e1",
                temperature=29.0,
                humidite=101.0,
                date_mesure=datetime.now(timezone.utc),
            )


class TestMesureIoTSchema:
    def test_payload_raspberry_pi_valide(self):
        m = MesureIoT(
            timestamp=1718615743,
            temperature=28.4,
            humidity=55.2,
            status="OK",
        )
        assert m.temperature == 28.4
        assert m.humidity == 55.2

    def test_status_defaut_ok(self):
        m = MesureIoT(
            timestamp=1718615743,
            temperature=29.0,
            humidity=55.0,
        )
        assert m.status == "OK"

    def test_to_mesure_data_convertit_les_champs(self):
        m = MesureIoT(timestamp=1718615743, temperature=28.4, humidity=55.2, status="OK")
        data = m.to_mesure_data(pays="bresil", entrepot="entrepot")
        assert data["humidite"] == 55.2
        assert data["statut"] == "ok"
        assert data["pays"] == "bresil"
        assert data["date_mesure"].year == 2024

    def test_to_mesure_data_timestamp_unix_vers_datetime(self):
        m = MesureIoT(timestamp=1718615743, temperature=28.4, humidity=55.2)
        data = m.to_mesure_data("bresil", "entrepot")
        from datetime import timezone
        assert data["date_mesure"].tzinfo == timezone.utc
