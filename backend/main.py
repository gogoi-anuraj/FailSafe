"""
FAILSAFE — FastAPI Backend
Entry point. Run with:  uvicorn main:app --reload
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config   import settings
from database import create_tables
from routes   import auth, predict, dashboard

logging.basicConfig(
    level   = logging.INFO,
    format  = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("failsafe")


# ── Lifespan ──────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Create DB tables
    logger.info("Creating database tables...")
    try:
      create_tables()
    except Exception as e:
      logger.error(f"DB error: {e}")

    # 2. Download + load ML models at startup
    # This runs BEFORE any request is served so the first
    # prediction request doesn't have to wait for download.
    logger.info("Loading ML models...")
    try:
        import model_loader
        model_loader.load_models()
    except Exception as e:
        # Log the error but don't crash the server.
        # Health check and auth endpoints still work.
        # Prediction endpoints will retry load_models() on first call.
        logger.error(f"Model loading failed at startup: {e}")

    logger.info("FAILSAFE API started.")
    yield
    logger.info("FAILSAFE API shutting down.")


# ── App ───────────────────────────────────────────────────────
app = FastAPI(
    title       = "FAILSAFE API",
    description = "Early student failure detection and intervention system.",
    version     = "1.0.0",
    lifespan    = lifespan,
)

# ── CORS ──────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins     = settings.origins,
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

# ── Routes ────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(predict.router)
app.include_router(dashboard.router)


# ── Health check ──────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "app": "FAILSAFE API", "version": "1.0.0"}


@app.get("/health", tags=["Health"])
def health():
    import model_loader
    return {
        "status"       : "healthy",
        "models_loaded": model_loader._loaded,
    }
