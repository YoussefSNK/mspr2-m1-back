from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.routes.central import router as central_router

settings = get_settings()

app = FastAPI(
    title="FutureKawa — Backend Central Siège",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(central_router)


@app.get("/health")
def health():
    return {"status": "ok", "role": "central"}
