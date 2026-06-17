"""
TDD — Tests du service email (sans envoi SMTP réel).
"""
import pytest
from unittest.mock import patch, MagicMock

from app.services.email_service import (
    get_email_responsable,
    build_email_body,
    send_alert_email,
)


class TestGetEmailResponsable:
    def test_bresil_retourne_email_bresil(self):
        email = get_email_responsable("bresil")
        assert "@" in email

    def test_equateur_retourne_email_equateur(self):
        email = get_email_responsable("equateur")
        assert "equateur" in email.lower() or "@" in email

    def test_colombie_retourne_email_colombie(self):
        email = get_email_responsable("colombie")
        assert "@" in email

    def test_pays_inconnu_leve_value_error(self):
        with pytest.raises(ValueError, match="Pays inconnu"):
            get_email_responsable("allemagne")


class TestBuildEmailBody:
    def test_corps_contient_entrepot(self):
        corps = build_email_body("bresil", "entrepot-1", "temperature_hors_seuil", "Temp 35°C")
        assert "entrepot-1" in corps

    def test_corps_contient_type_alerte(self):
        corps = build_email_body("bresil", "entrepot-1", "humidite_hors_seuil", "Hum 60%")
        assert "humidite_hors_seuil" in corps

    def test_corps_contient_message(self):
        msg = "Température critique détectée"
        corps = build_email_body("bresil", "entrepot-1", "temperature_hors_seuil", msg)
        assert msg in corps

    def test_corps_contient_futurekawa(self):
        corps = build_email_body("bresil", "entrepot-1", "temperature_hors_seuil", "msg")
        assert "FutureKawa" in corps


class TestSendAlertEmail:
    def test_smtp_non_configure_retourne_false_et_logue(self):
        result = send_alert_email("bresil", "entrepot-1", "temperature_hors_seuil", "test")
        assert result is False

    def test_smtp_configure_envoie_email(self):
        with patch("app.services.email_service.smtplib.SMTP") as mock_smtp_cls:
            mock_smtp = MagicMock()
            mock_smtp_cls.return_value.__enter__.return_value = mock_smtp

            with patch("app.services.email_service.get_settings") as mock_settings:
                settings = MagicMock()
                settings.SMTP_HOST = "smtp.real.com"
                settings.SMTP_PORT = 587
                settings.SMTP_USER = "user"
                settings.SMTP_PASSWORD = "pass"
                settings.SMTP_FROM = "noreply@futurekawa.com"
                settings.EMAIL_RESPONSABLE_BRESIL = "resp@futurekawa.com"
                mock_settings.return_value = settings

                result = send_alert_email(
                    "bresil", "entrepot-1", "temperature_hors_seuil", "Temp 35°C"
                )
                assert result is True
                mock_smtp.sendmail.assert_called_once()
