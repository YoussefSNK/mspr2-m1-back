"""
Scheduler léger — vérification périodique des lots trop anciens.

Le CDC exige une vérification automatique de la péremption des lots
(> 365 jours) avec une fréquence documentée. Plutôt que d'introduire une
dépendance lourde (APScheduler, Celery), on lance un thread daemon qui
appelle `verifier_lots_anciens` à intervalle régulier.

Le thread s'arrête proprement via un `threading.Event` : `stop()` réveille
immédiatement le `wait()` en cours, sans attendre la fin de l'intervalle.
"""
import logging
import threading

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.services.alert_service import verifier_lots_anciens

logger = logging.getLogger(__name__)


def _run_check() -> int:
    """Exécute une vérification. Retourne le nombre d'alertes créées.

    Chaque itération ouvre et ferme sa propre session pour éviter de garder
    une connexion ouverte pendant tout l'intervalle d'attente.
    """
    db = SessionLocal()
    try:
        alertes = verifier_lots_anciens(db)
        if alertes:
            logger.info("Scheduler : %d lot(s) trop ancien(s) détecté(s)", len(alertes))
        return len(alertes)
    except Exception as exc:  # une itération qui échoue ne doit pas tuer le thread
        logger.error("Scheduler : erreur pendant la vérification des lots : %s", exc)
        return 0
    finally:
        db.close()


class LotsScheduler:
    """Thread daemon exécutant `_run_check` à intervalle régulier."""

    def __init__(self, interval_seconds: int):
        self.interval_seconds = interval_seconds
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def _loop(self) -> None:
        logger.info(
            "Scheduler démarré — vérification des lots toutes les %d s",
            self.interval_seconds,
        )
        # Première vérification immédiate au démarrage, puis à intervalle régulier.
        _run_check()
        while not self._stop_event.wait(self.interval_seconds):
            _run_check()
        logger.info("Scheduler arrêté")

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._loop, name="lots-scheduler", daemon=True
        )
        self._thread.start()

    def stop(self, timeout: float = 5.0) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=timeout)


def start_scheduler() -> LotsScheduler | None:
    """Crée et démarre le scheduler si activé en configuration."""
    settings = get_settings()
    if not settings.SCHEDULER_ENABLED:
        logger.info("Scheduler désactivé (SCHEDULER_ENABLED=False)")
        return None

    scheduler = LotsScheduler(settings.SCHEDULER_INTERVAL_SECONDS)
    scheduler.start()
    return scheduler
