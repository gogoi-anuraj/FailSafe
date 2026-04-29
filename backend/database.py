"""
FAILSAFE — Database
SQLAlchemy engine, session, and table models.
Pool settings tuned for Render free tier (limited connections).
"""

from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String,
    Float, DateTime, Text, JSON, Boolean
)
from sqlalchemy.orm import declarative_base, sessionmaker

from config import settings

# ── Engine & Session ──────────────────────────────────────────
# Render free tier has limited DB connections — use conservative pool
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping   = True,   # reconnect if connection dropped
    pool_size       = 2,      # reduced for free tier
    max_overflow    = 3,      # max extra connections
    pool_recycle    = 280,    # recycle before Supabase 300s timeout
    pool_timeout    = 30,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ── Tables ────────────────────────────────────────────────────

class User(Base):
    """Faculty accounts."""
    __tablename__ = "users"

    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String(100), nullable=False)
    email      = Column(String(150), unique=True, index=True, nullable=False)
    password   = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Assessment(Base):
    """
    Stores each student assessment run.
    One row per student per upload batch.
    """
    __tablename__ = "assessments"

    id                 = Column(Integer, primary_key=True, index=True)
    batch_id           = Column(String(50), index=True)
    student_id         = Column(String(50), index=True)
    uploaded_by        = Column(Integer)
    risk_score         = Column(Float)
    risk_band          = Column(String(10))
    prediction         = Column(String(10))
    shap_values        = Column(JSON)
    top_factors        = Column(JSON)
    rule_interventions = Column(JSON)
    intervention_plan  = Column(Text)
    plan_source        = Column(String(10))
    student_data       = Column(JSON)
    created_at         = Column(DateTime, default=datetime.utcnow)


# ── Helpers ───────────────────────────────────────────────────

def get_db():
    """FastAPI dependency — yields a DB session, closes after request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all tables if they don't exist."""
    Base.metadata.create_all(bind=engine)
    print("Database tables ready.")
