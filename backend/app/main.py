from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.execute import router as execute_router
from app.api.quality_profiles import router as quality_profiles_router
from app.api.rollback import router as rollback_router
from app.api.rules import router as rules_router
from app.api.scan import router as scan_router
from app.api.settings import router as settings_router
from app.core.config import get_settings
from app.core.database import create_db_and_tables

settings = get_settings()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(settings_router)
app.include_router(rules_router)
app.include_router(quality_profiles_router)
app.include_router(scan_router)
app.include_router(execute_router)
app.include_router(rollback_router)


@app.on_event("startup")
def on_startup() -> None:
    create_db_and_tables()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
