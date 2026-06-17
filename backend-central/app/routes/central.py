from fastapi import APIRouter
from app.core.aggregator import aggregate_all, fetch_pays

router = APIRouter(prefix="/central", tags=["central"])


@router.get("/stocks")
async def get_stocks():
    return await aggregate_all("/api/lots/fifo")


@router.get("/lots")
async def get_lots():
    return await aggregate_all("/api/lots")


@router.get("/mesures")
async def get_mesures():
    return await aggregate_all("/api/mesures")


@router.get("/alertes")
async def get_alertes():
    return await aggregate_all("/api/alertes")


@router.get("/pays/{pays}/lots")
async def get_lots_par_pays(pays: str):
    data, error = await fetch_pays(pays, "/api/lots")
    if error:
        return {"error": error, "data": []}
    return {"data": data, "pays": pays}


@router.get("/pays/{pays}/alertes")
async def get_alertes_par_pays(pays: str):
    data, error = await fetch_pays(pays, "/api/alertes")
    if error:
        return {"error": error, "data": []}
    return {"data": data, "pays": pays}


@router.get("/pays/{pays}/mesures")
async def get_mesures_par_pays(pays: str):
    data, error = await fetch_pays(pays, "/api/mesures")
    if error:
        return {"error": error, "data": []}
    return {"data": data, "pays": pays}
