"""
Tests unitaires de l'agrégateur (app/core/aggregator.py).

On teste directement les fonctions async fetch_pays / aggregate_all,
en mockant les backends pays via respx. Ces tests couvrent les branches
d'erreur (pays inconnu, timeout, HTTP 500, indisponibilité) que les tests
de routes ne traversent pas isolément.
"""
import respx
import httpx

from app.core.aggregator import fetch_pays, aggregate_all


BRESIL_URL = "http://backend-bresil:8000"
EQUATEUR_URL = "http://backend-equateur:8000"
COLOMBIE_URL = "http://backend-colombie:8000"


class TestFetchPays:
    async def test_pays_inconnu_retourne_erreur(self):
        """Un pays absent de la table BACKENDS renvoie une erreur explicite,
        sans faire d'appel HTTP."""
        data, error = await fetch_pays("japon", "/api/lots")
        assert data is None
        assert error == "Pays inconnu : japon"

    @respx.mock
    async def test_succes_retourne_donnees(self):
        respx.get(f"{BRESIL_URL}/api/lots").mock(
            return_value=httpx.Response(200, json=[{"id": 1}])
        )
        data, error = await fetch_pays("bresil", "/api/lots")
        assert error is None
        assert data == [{"id": 1}]

    @respx.mock
    async def test_timeout_retourne_message_timeout(self):
        respx.get(f"{BRESIL_URL}/api/lots").mock(
            side_effect=httpx.TimeoutException("timed out")
        )
        data, error = await fetch_pays("bresil", "/api/lots")
        assert data is None
        assert "timeout" in error.lower()

    @respx.mock
    async def test_http_500_retourne_code_erreur(self):
        respx.get(f"{BRESIL_URL}/api/lots").mock(
            return_value=httpx.Response(500, json={"detail": "boom"})
        )
        data, error = await fetch_pays("bresil", "/api/lots")
        assert data is None
        assert "500" in error

    @respx.mock
    async def test_http_404_retourne_code_erreur(self):
        respx.get(f"{BRESIL_URL}/api/lots").mock(
            return_value=httpx.Response(404)
        )
        data, error = await fetch_pays("bresil", "/api/lots")
        assert data is None
        assert "404" in error

    @respx.mock
    async def test_connexion_refusee_retourne_indisponible(self):
        respx.get(f"{BRESIL_URL}/api/lots").mock(
            side_effect=httpx.ConnectError("refused")
        )
        data, error = await fetch_pays("bresil", "/api/lots")
        assert data is None
        assert "indisponible" in error.lower()


class TestAggregateAll:
    @respx.mock
    async def test_consolide_les_trois_pays(self):
        respx.get(f"{BRESIL_URL}/api/lots").mock(
            return_value=httpx.Response(200, json=[{"id": 1}, {"id": 2}])
        )
        respx.get(f"{EQUATEUR_URL}/api/lots").mock(
            return_value=httpx.Response(200, json=[{"id": 3}])
        )
        respx.get(f"{COLOMBIE_URL}/api/lots").mock(
            return_value=httpx.Response(200, json=[])
        )

        result = await aggregate_all("/api/lots")
        assert result["total"] == 3
        assert len(result["data"]) == 3
        assert result["errors"] == {}

    @respx.mock
    async def test_backend_en_erreur_est_liste_dans_errors(self):
        respx.get(f"{BRESIL_URL}/api/lots").mock(
            return_value=httpx.Response(200, json=[{"id": 1}])
        )
        respx.get(f"{EQUATEUR_URL}/api/lots").mock(
            side_effect=httpx.ConnectError("refused")
        )
        respx.get(f"{COLOMBIE_URL}/api/lots").mock(
            return_value=httpx.Response(500)
        )

        result = await aggregate_all("/api/lots")
        # Seul le Brésil a répondu -> consolidation partielle
        assert result["total"] == 1
        assert "equateur" in result["errors"]
        assert "colombie" in result["errors"]
        assert "bresil" not in result["errors"]

    @respx.mock
    async def test_tous_backends_en_erreur_total_zero(self):
        for url in (BRESIL_URL, EQUATEUR_URL, COLOMBIE_URL):
            respx.get(f"{url}/api/lots").mock(
                side_effect=httpx.ConnectError("refused")
            )

        result = await aggregate_all("/api/lots")
        assert result["total"] == 0
        assert result["data"] == []
        assert len(result["errors"]) == 3

    @respx.mock
    async def test_reponse_dict_non_liste_est_ignoree(self):
        """Si un backend renvoie un objet (dict) au lieu d'une liste,
        il n'est pas ajouté à la consolidation (branche isinstance list)."""
        respx.get(f"{BRESIL_URL}/api/lots").mock(
            return_value=httpx.Response(200, json={"message": "pas une liste"})
        )
        respx.get(f"{EQUATEUR_URL}/api/lots").mock(
            return_value=httpx.Response(200, json=[{"id": 1}])
        )
        respx.get(f"{COLOMBIE_URL}/api/lots").mock(
            return_value=httpx.Response(200, json=[])
        )

        result = await aggregate_all("/api/lots")
        # Le dict du Brésil est ignoré, seul l'Équateur compte
        assert result["total"] == 1
        assert result["errors"] == {}
