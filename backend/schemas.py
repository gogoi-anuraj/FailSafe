"""
FAILSAFE — Pydantic Schemas
Request and response shapes for all API endpoints.

StudentInput uses Field validators so bad values from the
form or CSV are rejected before reaching the model.
Binary yes/no fields use Literal[0,1] — anything else is refused.
Scale fields use ge/le bounds matching the dataset spec.
"""

from typing import Any, Dict, List, Literal, Optional, Tuple
from pydantic import BaseModel, EmailStr, Field


# ── Auth ──────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    name    : str
    email   : EmailStr
    password: str


class LoginRequest(BaseModel):
    email   : EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type  : str = "bearer"
    user_name   : str
    user_email  : str


# ── Prediction ────────────────────────────────────────────────

class StudentInput(BaseModel):
    """
    Single student feature input with strict validation.

    Faculty enter human-friendly values via dropdowns/toggles
    in the React form. The frontend maps labels to these numbers
    before sending. Values outside the allowed ranges are rejected
    with a 422 error before touching the model.
    """

    student_id : str

    # ── Grades & Absences ─────────────────────────────────────
    # Faculty enter raw numbers they already know
    G1      : int = Field(..., ge=0,  le=20,
                          description="First period grade (0–20)")
    G2      : int = Field(..., ge=0,  le=20,
                          description="Second period grade (0–20)")
    absences: int = Field(..., ge=0,  le=93,
                          description="Number of school absences")

    # ── Past Failures ─────────────────────────────────────────
    # Dropdown: None / 1 / 2 / 3 or more  →  0 / 1 / 2 / 3
    failures: int = Field(..., ge=0, le=3,
                          description="Past class failures (0=none, 3=three or more)")

    # ── Scale fields (1–4 range) ──────────────────────────────
    # Shown as labelled dropdowns in the form
    studytime : int = Field(..., ge=1, le=4,
                            description="Weekly study time (1=<2h, 2=2-5h, 3=5-10h, 4=>10h)")
    traveltime: int = Field(..., ge=1, le=4,
                            description="Travel time to school (1=<15m, 2=15-30m, 3=30m-1h, 4=>1h)")

    # ── Scale fields (1–5 range) ──────────────────────────────
    famrel  : int = Field(..., ge=1, le=5,
                          description="Family relationship quality (1=very bad, 5=excellent)")
    freetime: int = Field(..., ge=1, le=5,
                          description="Free time after school (1=very low, 5=very high)")
    goout   : int = Field(..., ge=1, le=5,
                          description="Going out with friends (1=very low, 5=very high)")
    Dalc    : int = Field(..., ge=1, le=5,
                          description="Weekday alcohol consumption (1=never, 5=very often)")
    Walc    : int = Field(..., ge=1, le=5,
                          description="Weekend alcohol consumption (1=never, 5=very often)")
    health  : int = Field(..., ge=1, le=5,
                          description="Current health status (1=very poor, 5=very good)")

    # ── Parent education (0–4 range) ──────────────────────────
    Medu: int = Field(..., ge=0, le=4,
                      description="Mother's education (0=none, 1 - primary education (4th grade), 2 – 5th to 9th grade, 3 – secondary education, 4=higher education)")
    Fedu: int = Field(..., ge=0, le=4,
                      description="Father's education (0=none, 1 - primary education (4th grade), 2 – 5th to 9th grade, 3 – secondary education, 4=higher education)")

    # ── Binary yes/no fields ──────────────────────────────────
    # Rendered as Yes/No toggles or radio buttons in the form
    # Only 0 or 1 accepted — anything else is a 422 error
    schoolsup : Literal[0, 1] = Field(..., description="Receiving extra school support? (0=No, 1=Yes)")
    famsup    : Literal[0, 1] = Field(..., description="Family provides study support? (0=No, 1=Yes)")
    paid      : Literal[0, 1] = Field(..., description="Attending extra paid classes? (0=No, 1=Yes)")
    activities: Literal[0, 1] = Field(..., description="In extracurricular activities? (0=No, 1=Yes)")
    higher    : Literal[0, 1] = Field(..., description="Wants to pursue higher education? (0=No, 1=Yes)")
    internet  : Literal[0, 1] = Field(..., description="Has internet access at home? (0=No, 1=Yes)")
    romantic  : Literal[0, 1] = Field(..., description="Currently in a romantic relationship? (0=No, 1=Yes)")

    class Config:
        json_schema_extra = {
            "example": {
                "student_id" : "STU-001",
                "G1"         : 9,
                "G2"         : 8,
                "absences"   : 12,
                "failures"   : 1,
                "studytime"  : 1,
                "traveltime" : 2,
                "famrel"     : 3,
                "freetime"   : 4,
                "goout"      : 4,
                "Dalc"       : 2,
                "Walc"       : 3,
                "health"     : 3,
                "Medu"       : 2,
                "Fedu"       : 1,
                "schoolsup"  : 0,
                "famsup"     : 1,
                "paid"       : 0,
                "activities" : 0,
                "higher"     : 1,
                "internet"   : 1,
                "romantic"   : 0,
            }
        }


class InterventionItem(BaseModel):
    feature      : str
    value        : Any
    shap         : float
    priority     : int
    category     : str
    intervention : str
    source       : str


class AssessmentResponse(BaseModel):
    student_id        : str
    risk_score        : float
    risk_band         : str
    prediction        : str
    top_factors       : List[Tuple[str, float]]
    rule_interventions: List[InterventionItem]
    intervention_plan : str
    plan_source       : str


# ── Batch ─────────────────────────────────────────────────────

class BatchSummaryItem(BaseModel):
    student_id        : str
    risk_score        : float
    risk_band         : str
    prediction        : str
    num_interventions : int
    top_category      : str


class BatchResponse(BaseModel):
    batch_id        : str
    total_students  : int
    high_risk       : int
    medium_risk     : int
    low_risk        : int
    at_risk_count   : int
    skipped_rows    : int    # rows that failed validation in CSV
    students        : List[BatchSummaryItem]


# ── Dashboard ─────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_assessed : int
    high_risk      : int
    medium_risk    : int
    low_risk       : int
    at_risk_count  : int
    avg_risk_score : float
    top_categories : List[Dict[str, Any]]
    recent_batches : List[Dict[str, Any]]
