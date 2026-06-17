import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_EMAIL_RESPONSABLES = {
    "bresil": "EMAIL_RESPONSABLE_BRESIL",
    "equateur": "EMAIL_RESPONSABLE_EQUATEUR",
    "colombie": "EMAIL_RESPONSABLE_COLOMBIE",
}


def get_email_responsable(pays: str) -> str:
    settings = get_settings()
    attr = _EMAIL_RESPONSABLES.get(pays)
    if attr is None:
        raise ValueError(f"Pays inconnu pour email : {pays}")
    return getattr(settings, attr)


def build_email_body(
    pays: str,
    entrepot: str,
    type_alerte: str,
    message: str,
) -> str:
    return (
        f"Bonjour,\n\n"
        f"Une alerte a été détectée dans l'entrepôt {entrepot} ({pays}).\n\n"
        f"Type : {type_alerte}\n"
        f"Détail : {message}\n\n"
        f"Action : vérifiez les conditions de stockage immédiatement.\n\n"
        f"FutureKawa — Système de monitoring"
    )


def send_alert_email(
    pays: str,
    entrepot: str,
    type_alerte: str,
    message: str,
) -> bool:
    settings = get_settings()
    destinataire = get_email_responsable(pays)
    sujet = f"[FutureKawa] Alerte stockage café - {pays.capitalize()}"
    corps = build_email_body(pays, entrepot, type_alerte, message)

    if not settings.SMTP_HOST or settings.SMTP_HOST == "smtp.example.com":
        logger.warning(
            "SMTP non configuré — email simulé | destinataire=%s | sujet=%s | corps=%s",
            destinataire,
            sujet,
            corps,
        )
        return False

    try:
        msg = MIMEMultipart()
        msg["From"] = settings.SMTP_FROM
        msg["To"] = destinataire
        msg["Subject"] = sujet
        msg.attach(MIMEText(corps, "plain", "utf-8"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            if settings.SMTP_USER:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM, destinataire, msg.as_string())

        logger.info("Email envoyé à %s pour alerte %s", destinataire, type_alerte)
        return True
    except Exception as exc:
        logger.error("Échec envoi email à %s : %s", destinataire, exc)
        return False
