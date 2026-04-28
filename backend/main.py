"""
FAILSAFE — FastAPI Backend
Entry point. Run with:  uvicorn main:app --reload
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config   import settings
from database import create_tables
from routes   import auth, predict, dashboard


# ── Lifespan — replaces deprecated @app.on_event ─────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs on startup
    create_tables()
    print("FAILSAFE API started.")
    yield
    # Runs on shutdown (add cleanup here if needed)
    print("FAILSAFE API shutting down.")


# ── App ───────────────────────────────────────────────────────
app = FastAPI(
    title       = "FAILSAFE API",
    description = "Early student failure detection and intervention system.",
    version     = "1.0.0",
    lifespan    = lifespan,
)

# ── CORS — allow React frontend ───────────────────────────────
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
    return {"status": "healthy"}
