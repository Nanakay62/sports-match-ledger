from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from packages.database.repository import LedgerRepository
from packages.database.session import engine

from .config import settings
from .routers import admin, claims, events, ingest, reliability, sources, topics


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    LedgerRepository.init_db(engine)
    from packages.database.registry import seed_initial_source_registry
    from packages.database.session import SessionLocal

    with SessionLocal() as session:
        seed_initial_source_registry(session)
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router, prefix="/api/v1")
app.include_router(events.router, prefix="/api/v1")
app.include_router(claims.router, prefix="/api/v1")
app.include_router(reliability.router, prefix="/api/v1")
app.include_router(sources.router, prefix="/api/v1")
app.include_router(topics.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")


@app.get("/healthz", tags=["health"])
def health_check():
    return {"status": "ok", "version": settings.app_version}
