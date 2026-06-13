"""
FAILSAFE — Prediction Routes

POST /predict                  — assess a single student (JSON body)
POST /predict-batch            — upload a CSV, assess all students
GET  /template                 — download empty CSV template
GET  /assessment/{id}          — retrieve a saved assessment by DB id
GET  /assessment/{id}/pdf      — export a single assessment as PDF
GET  /batch/{batch_id}         — retrieve all in a batch
GET  /batch/{batch_id}/pdf     — export entire batch as PDF report
DELETE /assessment/{id}        — delete one assessment
DELETE /batch/{batch_id}       — delete entire batch
DELETE /student/{student_id}   — delete all for a student
"""

import io
import uuid
from datetime import datetime
from typing import List

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from database            import get_db, Assessment
from schemas             import (StudentInput, AssessmentResponse,
                                 BatchResponse, BatchSummaryItem)
from auth                import get_current_user
from database            import User
import model_loader   
from intervention_engine_groq import run_full_assessment

router = APIRouter(tags=["Predictions"])


# ── Field validation rules (mirrors schemas.py) ───────────────
# Used to validate and clamp CSV rows before running the model.
FIELD_RULES = {
    "G1"        : {"min": 0,  "max": 20, "type": "int"},
    "G2"        : {"min": 0,  "max": 20, "type": "int"},
    "absences"  : {"min": 0,  "max": 93, "type": "int"},
    "failures"  : {"min": 0,  "max": 3,  "type": "int"},
    "studytime" : {"min": 1,  "max": 4,  "type": "int"},
    "traveltime": {"min": 1,  "max": 4,  "type": "int"},
    "famrel"    : {"min": 1,  "max": 5,  "type": "int"},
    "freetime"  : {"min": 1,  "max": 5,  "type": "int"},
    "goout"     : {"min": 1,  "max": 5,  "type": "int"},
    "Dalc"      : {"min": 1,  "max": 5,  "type": "int"},
    "Walc"      : {"min": 1,  "max": 5,  "type": "int"},
    "health"    : {"min": 1,  "max": 5,  "type": "int"},
    "Medu"      : {"min": 0,  "max": 4,  "type": "int"},
    "Fedu"      : {"min": 0,  "max": 4,  "type": "int"},
    "schoolsup" : {"min": 0,  "max": 1,  "type": "binary"},
    "famsup"    : {"min": 0,  "max": 1,  "type": "binary"},
    "paid"      : {"min": 0,  "max": 1,  "type": "binary"},
    "activities": {"min": 0,  "max": 1,  "type": "binary"},
    "higher"    : {"min": 0,  "max": 1,  "type": "binary"},
    "internet"  : {"min": 0,  "max": 1,  "type": "binary"},
    "romantic"  : {"min": 0,  "max": 1,  "type": "binary"},
}


def _validate_row(row: dict) -> tuple[dict, list[str]]:
    """
    Validate and clamp a CSV row's feature values.

    Returns:
        (cleaned_dict, errors)
        - cleaned_dict : values clamped to valid range
        - errors       : list of field-level error messages
    """
    cleaned = {}
    errors  = []

    for feat in model_loader.FEATURES:
        val  = row.get(feat)
        rule = FIELD_RULES.get(feat)

        # Missing value
        if val is None or (isinstance(val, float) and pd.isna(val)):
            errors.append(f"{feat}: missing value")
            continue

        # Try to cast to int
        try:
            val = int(float(val))
        except (ValueError, TypeError):
            errors.append(f"{feat}: not a number (got '{val}')")
            continue

        # Binary fields — must be exactly 0 or 1
        if rule and rule["type"] == "binary" and val not in (0, 1):
            errors.append(f"{feat}: must be 0 or 1 (got {val})")
            continue

        # Range check — clamp silently for scale fields
        if rule:
            if val < rule["min"]:
                val = rule["min"]
            elif val > rule["max"]:
                val = rule["max"]

        cleaned[feat] = val

    return cleaned, errors


# ── Helpers ───────────────────────────────────────────────────

def _save_assessment(db: Session, result: dict,
                      batch_id: str, user_id: int,
                      student_data: dict) -> Assessment:
    """Persist one assessment result to the database."""
    record = Assessment(
        batch_id           = batch_id,
        student_id         = result["student_id"],
        uploaded_by        = user_id,
        risk_score         = result["risk_score"],
        risk_band          = result["risk_band"],
        prediction         = result["prediction"],
        shap_values        = result["shap_values"],
        top_factors        = result["top_factors"],
        rule_interventions = result["rule_interventions"],
        intervention_plan  = result["intervention_plan"],
        plan_source        = result["plan_source"],
        student_data       = student_data,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def _result_to_response(result: dict) -> AssessmentResponse:
    """Convert engine output dict to Pydantic response."""
    return AssessmentResponse(
        student_id         = result["student_id"],
        risk_score         = result["risk_score"],
        risk_band          = result["risk_band"],
        prediction         = result["prediction"],
        top_factors        = result["top_factors"],
        rule_interventions = result["rule_interventions"],
        intervention_plan  = result["intervention_plan"],
        plan_source        = result["plan_source"],
    )


# ── CSV Template Download ─────────────────────────────────────

@router.get("/template", tags=["Predictions"])
def download_template():
    """
    Download an empty CSV template for batch upload.
    Faculty fill this in Excel/Sheets and upload it.
    Includes a sample row so faculty can see expected values.
    """
    # Header + one example row
    sample_row = {
        "student_id" : "STU-001",
        "G1"         : 10,
        "G2"         : 9,
        "absences"   : 5,
        "failures"   : 0,
        "studytime"  : 2,
        "traveltime" : 1,
        "famrel"     : 4,
        "freetime"   : 3,
        "goout"      : 3,
        "Dalc"       : 1,
        "Walc"       : 2,
        "health"     : 4,
        "Medu"       : 3,
        "Fedu"       : 2,
        "schoolsup"  : 0,
        "famsup"     : 1,
        "paid"       : 0,
        "activities" : 1,
        "higher"     : 1,
        "internet"   : 1,
        "romantic"   : 0,
    }

    df  = pd.DataFrame([sample_row])
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    buf.seek(0)

    return StreamingResponse(
        io.BytesIO(buf.getvalue().encode()),
        media_type = "text/csv",
        headers    = {
            "Content-Disposition": "attachment; filename=failsafe_template.csv"
        }
    )


# ── Single Student ────────────────────────────────────────────

@router.post("/predict", response_model=AssessmentResponse)
def predict_single(
    payload      : StudentInput,
    db           : Session = Depends(get_db),
    current_user : User    = Depends(get_current_user),
):
    """
    Assess a single student.
    Pydantic validates all field ranges before this runs.
    Runs model + SHAP + Groq intervention (with silent rule fallback).
    Saves result to DB and returns the full assessment.
    """
    student_data = payload.model_dump(exclude={"student_id"})

    try:
        result = run_full_assessment(
              student_id   = payload.student_id,
              student_data = student_data,
              model        = model_loader.MODEL,
              explainer    = model_loader.EXPLAINER,
              features     = model_loader.FEATURES,
              threshold    = model_loader.DECISION_THRESHOLD,
              use_llm      = True,
)
    except Exception as e:
        raise HTTPException(
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail      = f"Assessment failed: {str(e)}"
        )

    batch_id = f"single-{uuid.uuid4().hex[:8]}"
    _save_assessment(db, result, batch_id, current_user.id, student_data)

    return _result_to_response(result)


# ── Batch CSV Upload ──────────────────────────────────────────

@router.post("/predict-batch", response_model=BatchResponse)
def predict_batch(
    file         : UploadFile = File(...),
    db           : Session    = Depends(get_db),
    current_user : User       = Depends(get_current_user),
):
    """
    Upload a CSV file of students. Assesses all of them.

    - CSV must include all feature columns (download /template for the format)
    - student_id column is optional — row index used if absent
    - Binary fields (yes/no) must be 0 or 1 — rows with invalid binary values are skipped
    - Scale fields are clamped to valid range automatically
    - LLM is skipped in batch mode (use_llm=False) to save Groq credits
    - skipped_rows in the response tells faculty how many rows had issues
    """
    # ── Validate file type ────────────────────────────────────
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code = 400,
            detail      = "Only .csv files are accepted. Download the template from GET /template."
        )

    # ── Read CSV ──────────────────────────────────────────────
    try:
        contents = file.file.read()
        df       = pd.read_csv(io.BytesIO(contents))
    except Exception:
        raise HTTPException(status_code=400, detail="Could not read the CSV file. Check it is valid.")

    # ── Check required columns exist ──────────────────────────
    missing_cols = [f for f in model_loader.FEATURES if f not in df.columns]
    if missing_cols:
        raise HTTPException(
            status_code = 400,
            detail      = (
                f"CSV is missing required columns: {missing_cols}. "
                "Download the template from GET /template."
            )
        )

    # ── Run assessments ───────────────────────────────────────
    batch_id     = f"batch-{uuid.uuid4().hex[:8]}"
    summaries    : List[BatchSummaryItem] = []
    skipped_rows : int = 0

    for idx, row in df.iterrows():
        sid = str(row.get("student_id", idx))

        # Validate and clamp row values
        student_data, errors = _validate_row(row.to_dict())

        if errors:
            # Skip rows with binary violations or missing values
            skipped_rows += 1
            continue

        try:
            result = run_full_assessment(
               student_id   = sid,
               student_data = student_data,
               model        = model_loader.MODEL,
               explainer    = model_loader.EXPLAINER,
               features     = model_loader.FEATURES,
               threshold    = model_loader.DECISION_THRESHOLD,
               use_llm      = True,
            )
        except Exception:
            skipped_rows += 1
            continue

        _save_assessment(db, result, batch_id, current_user.id, student_data)

        top_cat = (
            result["rule_interventions"][0]["category"]
            if result["rule_interventions"] else "None"
        )
        summaries.append(BatchSummaryItem(
            student_id        = result["student_id"],
            risk_score        = result["risk_score"],
            risk_band         = result["risk_band"],
            prediction        = result["prediction"],
            num_interventions = len(result["rule_interventions"]),
            top_category      = top_cat,
        ))

    if not summaries:
        raise HTTPException(
            status_code = 400,
            detail      = (
                f"No valid student rows could be processed. "
                f"{skipped_rows} rows were skipped due to invalid values. "
                "Download the template from GET /template."
            )
        )

    bands = [s.risk_band for s in summaries]
    return BatchResponse(
        batch_id       = batch_id,
        total_students = len(summaries),
        high_risk      = bands.count("HIGH"),
        medium_risk    = bands.count("MEDIUM"),
        low_risk       = bands.count("LOW"),
        at_risk_count  = sum(1 for s in summaries if s.prediction == "AT-RISK"),
        skipped_rows   = skipped_rows,
        students       = sorted(summaries, key=lambda s: s.risk_score, reverse=True),
    )


# ── Get Saved Assessment ──────────────────────────────────────

@router.get("/assessment/{assessment_id}", response_model=AssessmentResponse)
def get_assessment(
    assessment_id: int,
    db           : Session = Depends(get_db),
    current_user : User    = Depends(get_current_user),
):
    """Retrieve a saved assessment by its database ID."""
    record = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Assessment not found.")

    return AssessmentResponse(
        student_id         = record.student_id,
        risk_score         = record.risk_score,
        risk_band          = record.risk_band,
        prediction         = record.prediction,
        top_factors        = record.top_factors,
        rule_interventions = record.rule_interventions,
        intervention_plan  = record.intervention_plan,
        plan_source        = record.plan_source,
    )


# ── Get Full Batch ────────────────────────────────────────────

@router.get("/batch/{batch_id}")
def get_batch(
    batch_id     : str,
    db           : Session = Depends(get_db),
    current_user : User    = Depends(get_current_user),
):
    """Retrieve all assessments belonging to a batch."""
    records = (
        db.query(Assessment)
        .filter(Assessment.batch_id == batch_id)
        .order_by(Assessment.risk_score.desc())
        .all()
    )
    if not records:
        raise HTTPException(status_code=404, detail="Batch not found.")

    return {
        "batch_id" : batch_id,
        "count"    : len(records),
        "students" : [
            {
                "id"               : r.id,
                "student_id"       : r.student_id,
                "risk_score"       : r.risk_score,
                "risk_band"        : r.risk_band,
                "prediction"       : r.prediction,
                "intervention_plan": r.intervention_plan,
                "created_at"       : r.created_at,
            }
            for r in records
        ],
    }


# ── Delete Single Assessment ──────────────────────────────────

@router.delete("/assessment/{assessment_id}")
def delete_assessment(
    assessment_id: int,
    db           : Session = Depends(get_db),
    current_user : User    = Depends(get_current_user),
):
    """
    Delete a single assessment by its database ID.
    Only the user who created it can delete it.
    """
    record = db.query(Assessment).filter(
        Assessment.id         == assessment_id,
        Assessment.uploaded_by == current_user.id,
    ).first()

    if not record:
        raise HTTPException(
            status_code = 404,
            detail      = "Assessment not found or you do not have permission to delete it."
        )

    db.delete(record)
    db.commit()

    return {"message": f"Assessment {assessment_id} deleted successfully."}


# ── Delete Entire Batch ───────────────────────────────────────

@router.delete("/batch/{batch_id}")
def delete_batch(
    batch_id     : str,
    db           : Session = Depends(get_db),
    current_user : User    = Depends(get_current_user),
):
    """
    Delete all assessments belonging to a batch.
    Only the user who uploaded it can delete it.
    """
    records = db.query(Assessment).filter(
        Assessment.batch_id    == batch_id,
        Assessment.uploaded_by == current_user.id,
    ).all()

    if not records:
        raise HTTPException(
            status_code = 404,
            detail      = "Batch not found or you do not have permission to delete it."
        )

    count = len(records)
    for record in records:
        db.delete(record)
    db.commit()

    return {
        "message"  : f"Batch '{batch_id}' deleted successfully.",
        "deleted"  : count,
    }


# ── Delete All Assessments for a Student ─────────────────────

@router.delete("/student/{student_id}")
def delete_student_assessments(
    student_id   : str,
    db           : Session = Depends(get_db),
    current_user : User    = Depends(get_current_user),
):
    """
    Delete all assessments for a specific student ID.
    Only the user who created them can delete them.
    """
    records = db.query(Assessment).filter(
        Assessment.student_id  == student_id,
        Assessment.uploaded_by == current_user.id,
    ).all()

    if not records:
        raise HTTPException(
            status_code = 404,
            detail      = "No assessments found for this student."
        )

    count = len(records)
    for record in records:
        db.delete(record)
    db.commit()

    return {
        "message" : f"All assessments for student '{student_id}' deleted.",
        "deleted" : count,
    }


# ── PDF Helper ────────────────────────────────────────────────

def _build_assessment_pdf(records: list, title: str) -> bytes:
    """
    Build a clean PDF report from a list of Assessment DB records.
    Uses only the standard library + reportlab (lightweight).
    Falls back to a plain-text PDF if reportlab not available.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles    import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units     import cm
        from reportlab.lib           import colors
        from reportlab.platypus      import (
            SimpleDocTemplate, Paragraph, Spacer,
            Table, TableStyle, HRFlowable
        )

        buf    = io.BytesIO()
        doc    = SimpleDocTemplate(buf, pagesize=A4,
                                   leftMargin=2*cm, rightMargin=2*cm,
                                   topMargin=2*cm,  bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        story  = []

        # ── Title ─────────────────────────────────────────────
        title_style = ParagraphStyle(
            'Title', parent=styles['Title'],
            fontSize=18, textColor=colors.HexColor('#6366F1'),
            spaceAfter=4
        )
        sub_style = ParagraphStyle(
            'Sub', parent=styles['Normal'],
            fontSize=9, textColor=colors.HexColor('#6B7280'),
            spaceAfter=16
        )
        body_style = ParagraphStyle(
            'Body', parent=styles['Normal'],
            fontSize=9, leading=13,
            textColor=colors.HexColor('#1A1D23')
        )
        label_style = ParagraphStyle(
            'Label', parent=styles['Normal'],
            fontSize=7, textColor=colors.HexColor('#6B7280'),
            spaceAfter=2
        )

        story.append(Paragraph('FAILSAFE', title_style))
        story.append(Paragraph(title, ParagraphStyle(
            'H1', parent=styles['Heading1'], fontSize=13, spaceAfter=2
        )))
        story.append(Paragraph(
            f'Generated: {datetime.utcnow().strftime("%d %b %Y, %H:%M UTC")} · '
            f'{len(records)} record(s)',
            sub_style
        ))
        story.append(HRFlowable(width='100%', thickness=1,
                                 color=colors.HexColor('#E5E7EB'), spaceAfter=16))

        for r in records:
            # ── Risk header ───────────────────────────────────
            band_colors = {'HIGH': '#EF4444', 'MEDIUM': '#F59E0B', 'LOW': '#10B981'}
            band_color  = band_colors.get(r.risk_band, '#6B7280')

            header_data = [[
                Paragraph(f'<b>Student: {r.student_id}</b>',
                          ParagraphStyle('SH', parent=styles['Normal'], fontSize=11)),
                Paragraph(
                    f'<font color="{band_color}"><b>{r.risk_band} RISK — {r.risk_score}%</b></font>',
                    ParagraphStyle('RH', parent=styles['Normal'], fontSize=11,
                                   alignment=2)
                ),
            ]]
            header_table = Table(header_data, colWidths=['60%', '40%'])
            header_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F9FAFB')),
                ('ROUNDEDCORNERS', [4]),
                ('TOPPADDING',    (0,0), (-1,-1), 8),
                ('BOTTOMPADDING', (0,0), (-1,-1), 8),
                ('LEFTPADDING',   (0,0), (-1,-1), 10),
                ('RIGHTPADDING',  (0,0), (-1,-1), 10),
            ]))
            story.append(header_table)
            story.append(Spacer(1, 8))

            # ── Meta row ──────────────────────────────────────
            meta_data = [[
                Paragraph(f'Prediction: <b>{r.prediction}</b>', body_style),
                Paragraph(f'Batch: <b>{r.batch_id}</b>', body_style),
                Paragraph(f'Date: <b>{r.created_at.strftime("%d %b %Y")}</b>', body_style),
            ]]
            meta_table = Table(meta_data, colWidths=['33%', '33%', '34%'])
            meta_table.setStyle(TableStyle([
                ('TOPPADDING',    (0,0), (-1,-1), 0),
                ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ]))
            story.append(meta_table)
            story.append(Spacer(1, 10))

            # ── Top risk factors ──────────────────────────────
            if r.top_factors:
                story.append(Paragraph('Key Risk Factors', label_style))
                factors = r.top_factors[:5]
                factor_data = [['Feature', 'SHAP Value', 'Direction']] + [
                    [
                        f[0],
                        f'{f[1]:+.4f}',
                        'Increases risk' if f[1] > 0 else 'Reduces risk'
                    ]
                    for f in factors
                ]
                factor_table = Table(factor_data, colWidths=['40%', '25%', '35%'])
                factor_table.setStyle(TableStyle([
                    ('BACKGROUND',    (0,0), (-1,0),  colors.HexColor('#F3F4F6')),
                    ('FONTSIZE',      (0,0), (-1,-1), 8),
                    ('TOPPADDING',    (0,0), (-1,-1), 4),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                    ('LEFTPADDING',   (0,0), (-1,-1), 6),
                    ('GRID',          (0,0), (-1,-1), 0.5, colors.HexColor('#E5E7EB')),
                    ('FONTNAME',      (0,0), (-1,0),  'Helvetica-Bold'),
                    ('TEXTCOLOR',     (1,1), (1,-1),
                     colors.HexColor('#EF4444') if True else colors.black),
                ]))
                # Color SHAP values individually
                for row_i, f in enumerate(factors, 1):
                    col_color = colors.HexColor('#DC2626') if f[1] > 0 else colors.HexColor('#059669')
                    factor_table.setStyle(TableStyle([
                        ('TEXTCOLOR', (1, row_i), (1, row_i), col_color),
                        ('TEXTCOLOR', (2, row_i), (2, row_i), col_color),
                    ]))
                story.append(factor_table)
                story.append(Spacer(1, 10))

            # ── Intervention plan ─────────────────────────────
            if r.intervention_plan:
                story.append(Paragraph('Faculty Action Plan', label_style))
                story.append(Paragraph(r.intervention_plan, ParagraphStyle(
                    'Plan', parent=styles['Normal'], fontSize=9,
                    leading=14, textColor=colors.HexColor('#374151'),
                    borderPadding=(8, 8, 8, 8),
                    borderColor=colors.HexColor('#E5E7EB'),
                    borderWidth=1, borderRadius=4,
                    backColor=colors.HexColor('#FAFAFA'),
                    spaceAfter=8
                )))

            # ── Interventions table ───────────────────────────
            if r.rule_interventions:
                story.append(Paragraph('Intervention Actions', label_style))
                priority_labels = {1: 'URGENT', 2: 'MODERATE', 3: 'ADVISORY'}
                priority_colors = {
                    1: colors.HexColor('#DC2626'),
                    2: colors.HexColor('#D97706'),
                    3: colors.HexColor('#2563EB'),
                }
                for item in r.rule_interventions:
                    p      = item.get('priority', 3)
                    p_col  = priority_colors.get(p, colors.HexColor('#6B7280'))
                    p_lbl  = priority_labels.get(p, 'ADVISORY')
                    row_data = [[
                        Paragraph(
                            f'<font color="#{p_col.hexval()[2:]}"><b>{p_lbl}</b></font>  '
                            f'{item.get("category","")}',
                            ParagraphStyle('IP', parent=styles['Normal'], fontSize=8)
                        ),
                        Paragraph(item.get('intervention', ''), ParagraphStyle(
                            'IT', parent=styles['Normal'], fontSize=8, leading=12
                        )),
                    ]]
                    int_table = Table(row_data, colWidths=['25%', '75%'])
                    int_table.setStyle(TableStyle([
                        ('TOPPADDING',    (0,0), (-1,-1), 4),
                        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                        ('LEFTPADDING',   (0,0), (-1,-1), 6),
                        ('LINEBELOW',     (0,0), (-1,-1), 0.5,
                         colors.HexColor('#F3F4F6')),
                        ('VALIGN',        (0,0), (-1,-1), 'TOP'),
                    ]))
                    story.append(int_table)

            story.append(Spacer(1, 20))
            story.append(HRFlowable(width='100%', thickness=0.5,
                                     color=colors.HexColor('#E5E7EB'), spaceAfter=16))

        doc.build(story)
        return buf.getvalue()

    except ImportError:
        # Reportlab not installed — return plain text as PDF fallback
        lines = [f'FAILSAFE — {title}',
                 f'Generated: {datetime.utcnow().strftime("%d %b %Y %H:%M UTC")}',
                 '=' * 60]
        for r in records:
            lines += [
                f'',
                f'Student   : {r.student_id}',
                f'Risk Score: {r.risk_score}%  ({r.risk_band})',
                f'Prediction: {r.prediction}',
                f'Batch     : {r.batch_id}',
                f'Date      : {r.created_at.strftime("%d %b %Y")}',
                f'',
                f'Action Plan:',
                r.intervention_plan or 'N/A',
                '-' * 60,
            ]
        content = '\n'.join(lines).encode('utf-8')
        return content


# ── Export Single Assessment as PDF ──────────────────────────

@router.get("/assessment/{assessment_id}/pdf")
def export_assessment_pdf(
    assessment_id: int,
    db           : Session = Depends(get_db),
    current_user : User    = Depends(get_current_user),
):
    """Export a single assessment as a PDF report."""
    record = db.query(Assessment).filter(
        Assessment.id         == assessment_id,
        Assessment.uploaded_by == current_user.id,
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="Assessment not found.")

    pdf_bytes = _build_assessment_pdf(
        [record],
        title=f'Assessment Report — {record.student_id}'
    )

    filename = f'failsafe_{record.student_id}_{record.created_at.strftime("%Y%m%d")}.pdf'

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type = 'application/pdf',
        headers    = {'Content-Disposition': f'attachment; filename="{filename}"'}
    )


# ── Export Entire Batch as PDF ────────────────────────────────

@router.get("/batch/{batch_id}/pdf")
def export_batch_pdf(
    batch_id     : str,
    db           : Session = Depends(get_db),
    current_user : User    = Depends(get_current_user),
):
    """Export all assessments in a batch as a single PDF report."""
    records = (
        db.query(Assessment)
        .filter(
            Assessment.batch_id    == batch_id,
            Assessment.uploaded_by == current_user.id,
        )
        .order_by(Assessment.risk_score.desc())
        .all()
    )

    if not records:
        raise HTTPException(status_code=404, detail="Batch not found.")

    pdf_bytes = _build_assessment_pdf(
        records,
        title=f'Batch Report — {batch_id} ({len(records)} students)'
    )

    filename = f'failsafe_batch_{batch_id}.pdf'

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type = 'application/pdf',
        headers    = {'Content-Disposition': f'attachment; filename="{filename}"'}
    )
