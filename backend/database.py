"""
FAILSAFE — Database
SQLAlchemy engine, session, and table models.
"""

from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String,
    Float, DateTime, Text, JSON, Boolean
)
from sqlalchemy.orm import declarative_base, sessionmaker

from config import settings

# ── Engine & Session ──────────────────────────────────────────
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,      # reconnect if connection dropped
    pool_size=5,
    max_overflow=10,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ── Tables ────────────────────────────────────────────────────

class User(Base):
    """Faculty / HOD accounts."""
    __tablename__ = "users"

    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String(100), nullable=False)
    email      = Column(String(150), unique=True, index=True, nullable=False)
    password   = Column(String(255), nullable=False)   # bcrypt hash
    created_at = Column(DateTime, default=datetime.utcnow)


class Assessment(Base):
    """
    Stores each student assessment run.
    One row per student per upload batch.
    """
    __tablename__ = "assessments"

    id                = Column(Integer, primary_key=True, index=True)
    batch_id          = Column(String(50), index=True)     # groups a CSV upload
    student_id        = Column(String(50), index=True)
    uploaded_by       = Column(Integer)                    # user.id
    risk_score        = Column(Float)
    risk_band         = Column(String(10))                 # LOW / MEDIUM / HIGH
    prediction        = Column(String(10))                 # AT-RISK / PASSING
    shap_values       = Column(JSON)                       # {feature: shap_val}
    top_factors       = Column(JSON)                       # [[feat, val], ...]
    rule_interventions= Column(JSON)                       # list of rule dicts
    intervention_plan = Column(Text)                       # LLM or rule narrative
    plan_source       = Column(String(10))                 # 'llm' or 'rules'
    student_data      = Column(JSON)                       # original feature values
    created_at        = Column(DateTime, default=datetime.utcnow)


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
    print("Database tables created.")
