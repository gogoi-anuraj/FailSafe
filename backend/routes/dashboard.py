"""
FAILSAFE — Dashboard Routes

GET /dashboard/stats    — overall stats across all assessments
GET /dashboard/history  — recent batches uploaded by this user
GET /dashboard/student/{student_id} — all assessments for a student
"""

from collections import Counter
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from database  import get_db, Assessment
from schemas   import DashboardStats
from auth      import get_current_user
from database  import User

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStats)
def get_stats(
    db           : Session = Depends(get_db),
    current_user : User    = Depends(get_current_user),
):
    """
    Returns overall stats for all assessments uploaded by this user.
    Used to populate the main dashboard cards and charts.
    """
    records = (
        db.query(Assessment)
        .filter(Assessment.uploaded_by == current_user.id)
        .all()
    )

    if not records:
        return DashboardStats(
            total_assessed = 0,
            high_risk      = 0,
            medium_risk    = 0,
            low_risk       = 0,
            at_risk_count  = 0,
            avg_risk_score = 0.0,
            top_categories = [],
            recent_batches = [],
        )

    bands      = [r.risk_band  for r in records]
    scores     = [r.risk_score for r in records]
    at_risk    = sum(1 for r in records if r.prediction == "AT-RISK")

    # Most triggered intervention categories
    all_categories = []
    for r in records:
        if r.rule_interventions:
            for item in r.rule_interventions:
                all_categories.append(item.get("category", ""))
    cat_counts = [
        {"category": cat, "count": cnt}
        for cat, cnt in Counter(all_categories).most_common(5)
    ]

    # Recent batches
    batch_ids = list(dict.fromkeys(r.batch_id for r in reversed(records)))[:5]
    recent_batches = []
    for bid in batch_ids:
        batch_records = [r for r in records if r.batch_id == bid]
        recent_batches.append({
            "batch_id"     : bid,
            "count"        : len(batch_records),
            "high_risk"    : sum(1 for r in batch_records if r.risk_band == "HIGH"),
            "at_risk"      : sum(1 for r in batch_records if r.prediction == "AT-RISK"),
            "uploaded_at"  : batch_records[0].created_at,
        })

    return DashboardStats(
        total_assessed = len(records),
        high_risk      = bands.count("HIGH"),
        medium_risk    = bands.count("MEDIUM"),
        low_risk       = bands.count("LOW"),
        at_risk_count  = at_risk,
        avg_risk_score = round(sum(scores) / len(scores), 1),
        top_categories = cat_counts,
        recent_batches = recent_batches,
    )


@router.get("/history")
def get_history(
    db           : Session = Depends(get_db),
    current_user : User    = Depends(get_current_user),
):
    """
    Returns the most recent 50 assessments uploaded by this user,
    ordered by newest first. Used to populate the assessments table.
    """
    records = (
        db.query(Assessment)
        .filter(Assessment.uploaded_by == current_user.id)
        .order_by(Assessment.created_at.desc())
        .limit(50)
        .all()
    )

    return {
        "count"  : len(records),
        "records": [
            {
                "id"               : r.id,
                "batch_id"         : r.batch_id,
                "student_id"       : r.student_id,
                "risk_score"       : r.risk_score,
                "risk_band"        : r.risk_band,
                "prediction"       : r.prediction,
                "top_factors"      : r.top_factors,
                "intervention_plan": r.intervention_plan,
                "created_at"       : r.created_at,
            }
            for r in records
        ],
    }


@router.get("/student/{student_id}")
def get_student_history(
    student_id   : str,
    db           : Session = Depends(get_db),
    current_user : User    = Depends(get_current_user),
):
    """
    All assessments for a specific student ID across all batches.
    Useful for tracking a student's risk trend over the semester.
    """
    records = (
        db.query(Assessment)
        .filter(
            Assessment.uploaded_by == current_user.id,
            Assessment.student_id  == student_id,
        )
        .order_by(Assessment.created_at.asc())
        .all()
    )

    if not records:
        return {"student_id": student_id, "count": 0, "history": []}

    return {
        "student_id": student_id,
        "count"     : len(records),
        "latest"    : {
            "risk_score": records[-1].risk_score,
            "risk_band" : records[-1].risk_band,
            "prediction": records[-1].prediction,
        },
        "trend"     : [
            {
                "date"      : r.created_at,
                "risk_score": r.risk_score,
                "risk_band" : r.risk_band,
                "prediction": r.prediction,
            }
            for r in records
        ],
        "history"   : [
            {
                "id"               : r.id,
                "batch_id"         : r.batch_id,
                "risk_score"       : r.risk_score,
                "risk_band"        : r.risk_band,
                "prediction"       : r.prediction,
                "intervention_plan": r.intervention_plan,
                "created_at"       : r.created_at,
            }
            for r in records
        ],
    }
