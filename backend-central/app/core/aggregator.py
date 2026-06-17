"""
Client HTTP vers les backends pays. Gère les erreurs de disponibilité proprement.
"""
import logging
import httpx
from app.core.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

BACKENDS: dict[str, str] = {
    "bresil": settings.BACKEND_BRESIL_URL,
    "equateur": settings.BACKEND_EQUATEUR_URL,
    "colombie": settings.BACKEND_COLOMBIE_URL,
}


async def fetch_pays(pays: str, path: str) -> tuple[list | dict | None, str | None]:
    """
    Retourne (données, None) ou (None, message_erreur).
    """
    base_url = BACKENDS.get(pays)
    if not base_url:
        return None, f"Pays inconnu : {pays}"

    url = f"{base_url}{path}"
    try:
        async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json(), None
    except httpx.TimeoutException:
        logger.warning("Timeout vers backend %s (%s)", pays, url)
        return None, f"Backend {pays} timeout"
    except httpx.HTTPStatusError as e:
        logger.warning("HTTP %d depuis backend %s", e.response.status_code, pays)
        return None, f"Backend {pays} erreur {e.response.status_code}"
    except Exception as exc:
        logger.warning("Erreur backend %s : %s", pays, exc)
        return None, f"Backend {pays} indisponible"


async def aggregate_all(path: str) -> dict:
    """
    Appelle tous les backends pays en parallèle et consolide les résultats.
    """
    import asyncio

    tasks = {pays: fetch_pays(pays, path) for pays in BACKENDS}
    results = await asyncio.gather(*tasks.values(), return_exceptions=False)

    consolidated: list = []
    errors: dict[str, str] = {}
    for pays, (data, error) in zip(tasks.keys(), results):
        if error:
            errors[pays] = error
        elif isinstance(data, list):
            consolidated.extend(data)

    return {"data": consolidated, "errors": errors, "total": len(consolidated)}
