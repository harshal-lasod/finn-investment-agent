"""FINN API application."""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router
from backend.config import settings
from backend.database import init_db, load_portfolio_seed


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    seed_path = Path(__file__).resolve().parent / "storage" / "portfolio_seed.json"
    await load_portfolio_seed(settings.DATABASE_URL, str(seed_path))
    yield

app = FastAPI(
    title="FINN — Financial Investment Agent",
    description="Mobile-first demo for portfolio intelligence, research, and network discovery.",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router, prefix="/api")


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    return {"status": "healthy", "service": "FINN", "version": "1.0.0"}
