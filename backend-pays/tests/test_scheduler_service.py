"""
Tests du scheduler de vérification des lots anciens.

On isole le comportement du thread (démarrage, appel périodique, arrêt propre)
en mockant `verifier_lots_anciens` et la session DB — la logique métier
elle-même est déjà couverte par test_alert_rules / test_routes_alertes.
"""
import time
from unittest.mock import patch, MagicMock

from app.services import scheduler_service
from app.services.scheduler_service import LotsScheduler, start_scheduler


class TestRunCheck:
    def test_run_check_appelle_verifier_et_ferme_session(self):
        fake_session = MagicMock()
        with patch.object(scheduler_service, "SessionLocal", return_value=fake_session), \
             patch.object(scheduler_service, "verifier_lots_anciens", return_value=[1, 2]) as m_verif:
            count = scheduler_service._run_check()

        assert count == 2
        m_verif.assert_called_once_with(fake_session)
        fake_session.close.assert_called_once()

    def test_run_check_erreur_ne_propage_pas_et_ferme_session(self):
        """Une exception pendant la vérification est avalée (le thread survit)
        et la session est tout de même fermée."""
        fake_session = MagicMock()
        with patch.object(scheduler_service, "SessionLocal", return_value=fake_session), \
             patch.object(scheduler_service, "verifier_lots_anciens", side_effect=RuntimeError("boom")):
            count = scheduler_service._run_check()

        assert count == 0
        fake_session.close.assert_called_once()


class TestLotsScheduler:
    def test_execute_verification_immediate_au_demarrage(self):
        with patch.object(scheduler_service, "_run_check") as m_check:
            sched = LotsScheduler(interval_seconds=3600)  # long : une seule passe
            sched.start()
            time.sleep(0.1)  # laisse le thread démarrer et faire la 1re passe
            sched.stop()

        assert m_check.call_count >= 1

    def test_appels_periodiques_sur_petit_intervalle(self):
        with patch.object(scheduler_service, "_run_check") as m_check:
            sched = LotsScheduler(interval_seconds=0.05)
            sched.start()
            time.sleep(0.25)  # ~1 immédiat + plusieurs itérations
            sched.stop()

        # 1 passe immédiate + au moins 2 itérations sur 0.25 s à 0.05 s d'intervalle
        assert m_check.call_count >= 3

    def test_stop_arrete_le_thread(self):
        with patch.object(scheduler_service, "_run_check"):
            sched = LotsScheduler(interval_seconds=3600)
            sched.start()
            time.sleep(0.05)
            assert sched._thread.is_alive()
            sched.stop()
            assert not sched._thread.is_alive()

    def test_start_idempotent_ne_lance_pas_deux_threads(self):
        with patch.object(scheduler_service, "_run_check"):
            sched = LotsScheduler(interval_seconds=3600)
            sched.start()
            first_thread = sched._thread
            sched.start()  # second appel : ne doit pas remplacer le thread
            assert sched._thread is first_thread
            sched.stop()


class TestStartScheduler:
    def test_desactive_retourne_none(self):
        fake_settings = MagicMock(SCHEDULER_ENABLED=False)
        with patch.object(scheduler_service, "get_settings", return_value=fake_settings):
            result = start_scheduler()
        assert result is None

    def test_active_retourne_scheduler_demarre(self):
        fake_settings = MagicMock(SCHEDULER_ENABLED=True, SCHEDULER_INTERVAL_SECONDS=3600)
        with patch.object(scheduler_service, "get_settings", return_value=fake_settings), \
             patch.object(scheduler_service, "_run_check"):
            result = start_scheduler()
            assert isinstance(result, LotsScheduler)
            assert result._thread.is_alive()
            result.stop()
