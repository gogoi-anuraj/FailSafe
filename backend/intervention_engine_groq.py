"""
FAILSAFE — Intervention Engine
intervention_engine.py

Imported by FastAPI. Uses Groq LLM to generate personalized
intervention plans. Falls back to rule-based text silently
on any Groq failure — no error surfaces to the user.
"""

import os
import time
import logging
import pandas as pd
from typing import List, Dict, Any, Tuple

logger = logging.getLogger("failsafe.intervention")

# ── Groq config ───────────────────────────────────────────────
GROQ_API_KEY    = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL      = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_FALLBACK   = "llama-3.1-8b-instant"
GROQ_MAX_TOKENS = 500
GROQ_TIMEOUT    = 8

try:
    from groq import Groq
    _groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
except Exception:
    _groq_client = None


# ── Intervention Rules ────────────────────────────────────────
INTERVENTION_RULES = {
    "absences"  : {"bad_when": "high", "threshold": 6,  "priority": 1,
                   "category": "Attendance",
                   "intervention": "Student has high absences. Schedule an immediate one-on-one attendance review with the class advisor. Identify whether absences are health-related, family-related, or motivational. Issue a formal attendance warning if absences exceed 10."},

    "failures"  : {"bad_when": "high", "threshold": 1,  "priority": 1,
                   "category": "Academic History",
                   "intervention": "Student has a history of past failures. Assign a dedicated academic mentor for weekly check-ins. Enroll student in remedial support classes. Set up monthly progress reviews with the HOD."},

    "G2"        : {"bad_when": "low",  "threshold": 10, "priority": 1,
                   "category": "Academic Performance",
                   "intervention": "Student scored below passing in the second period. Provide targeted tutoring sessions before the final exam. Review second period papers with the student to identify weak topics. Schedule bi-weekly progress checks with subject teacher."},

    "G1"        : {"bad_when": "low",  "threshold": 10, "priority": 2,
                   "category": "Academic Performance",
                   "intervention": "Student showed early signs of struggle in the first period. Conduct a diagnostic assessment to identify knowledge gaps. Pair with a higher-performing peer for study support."},

    # Threshold raised from 2 to 3 — catches borderline low studytime
    "studytime" : {"bad_when": "low",  "threshold": 3,  "priority": 2,
                   "category": "Study Habits",
                   "intervention": "Student reports low weekly study time. Introduce a structured timetable with the class advisor. Recommend the institution study skills workshop."},

    "Dalc"      : {"bad_when": "high", "threshold": 3,  "priority": 1,
                   "category": "Wellness",
                   "intervention": "Student has high weekday alcohol consumption. Refer to the student counselling or wellness center immediately. Coordinate with the guardian if appropriate."},

    "Walc"      : {"bad_when": "high", "threshold": 3,  "priority": 2,
                   "category": "Wellness",
                   "intervention": "Student has elevated weekend alcohol consumption. Suggest a confidential wellness session. Monitor for impacts on Monday attendance."},

    # Threshold lowered from 4 to 3 — catches moderate social distraction
    "goout"     : {"bad_when": "high", "threshold": 3,  "priority": 2,
                   "category": "Time Management",
                   "intervention": "Student spends significant time socializing. Discuss time management strategies. Help create a balanced weekly schedule combining social and study time."},

    "health"    : {"bad_when": "low",  "threshold": 3,  "priority": 2,
                   "category": "Health Support",
                   "intervention": "Student reports below average health status. Refer to the campus health center. Explore whether academic accommodations are needed."},

    "higher"    : {"bad_when": "low",  "threshold": 1,  "priority": 2,
                   "category": "Motivation",
                   "intervention": "Student does not aspire to higher education. Schedule a career counselling session. Connect with alumni or industry mentors to inspire motivation."},

    "internet"  : {"bad_when": "low",  "threshold": 1,  "priority": 3,
                   "category": "Resource Access",
                   "intervention": "Student lacks internet at home. Direct to campus Wi-Fi, computer labs, and printed materials."},

    "Medu"      : {"bad_when": "low",  "threshold": 2,  "priority": 3,
                   "category": "Family Background",
                   "intervention": "Student comes from a low parental education background. Assign a faculty mentor and connect with first-generation student support."},

    "Fedu"      : {"bad_when": "low",  "threshold": 2,  "priority": 3,
                   "category": "Family Background",
                   "intervention": "Father has low education level. Ensure access to faculty office hours. Recommend peer tutoring programs."},

    # Threshold raised from 2 to 3 — catches poor family relations, not just very bad
    "famrel"    : {"bad_when": "low",  "threshold": 3,  "priority": 2,
                   "category": "Family & Wellbeing",
                   "intervention": "Student reports below average family relationship quality. Refer to a student counsellor for emotional support. Monitor for signs of stress or disengagement."},

    "schoolsup" : {"bad_when": "low",  "threshold": 1,  "priority": 2,
                   "category": "Academic Support",
                   "intervention": "Student is not receiving school support. Enroll in the academic support program. Assign a subject teacher for additional sessions."},

    "famsup"    : {"bad_when": "low",  "threshold": 1,  "priority": 3,
                   "category": "Family Support",
                   "intervention": "Student lacks family educational support. Increase faculty check-ins. Share progress updates with guardians."},

    "romantic"  : {"bad_when": "high", "threshold": 1,  "priority": 3,
                   "category": "Personal Factors",
                   "intervention": "Student is in a romantic relationship which may affect focus. Counsel sensitively on balancing personal and academic life."},

    "traveltime": {"bad_when": "high", "threshold": 3,  "priority": 3,
                   "category": "Logistics",
                   "intervention": "Student has a long daily commute. Explore campus accommodation options. Consider scheduling sessions at favorable times."},

    # Threshold lowered from 4 to 3 — catches moderate excess free time
    "freetime"  : {"bad_when": "high", "threshold": 3,  "priority": 3,
                   "category": "Time Management",
                   "intervention": "Student reports high free time indicating possible low engagement. Encourage joining academic clubs or project groups."},

    "paid"      : {"bad_when": "low",  "threshold": 1,  "priority": 3,
                   "category": "Academic Support",
                   "intervention": "Student is not attending extra classes. Recommend free campus tutoring or peer study groups."},

    "activities": {"bad_when": "low",  "threshold": 1,  "priority": 3,
                   "category": "Engagement",
                   "intervention": "Student is not involved in extracurricular activities. Encourage joining at least one club or sport."},
}


# ── Risk Band ─────────────────────────────────────────────────

def get_risk_band(prob: float, low: float = 0.35, high: float = 0.65) -> str:
    if prob >= high:
        return "HIGH"
    elif prob >= low:
        return "MEDIUM"
    return "LOW"


# ── Rule-Based Interventions ──────────────────────────────────

def generate_rule_interventions(student_data: Dict,
                                 shap_values_dict: Dict,
                                 top_n: int = 5) -> List[Dict]:
    """
    Generate rule-based intervention list from SHAP factors.
    Only triggers when the feature value is genuinely in the risky direction.
    SHAP magnitude alone does NOT trigger an intervention — the value must
    also be bad (e.g. G2=20 never triggers even if SHAP is large).
    """
    ranked = sorted(shap_values_dict.items(),
                    key=lambda x: abs(x[1]), reverse=True)[:top_n]
    interventions = []

    for feat, shap_val in ranked:
        if feat not in INTERVENTION_RULES:
            continue
        rule = INTERVENTION_RULES[feat]
        val  = student_data.get(feat)
        if val is None:
            continue

        is_risky = (
            (rule["bad_when"] == "high" and val >= rule["threshold"]) or
            (rule["bad_when"] == "low"  and val <  rule["threshold"])
        )

        # Only add if the value is genuinely risky.
        # Removed the abs(shap_val) > 0.2 fallback — it was causing
        # good values (e.g. G2=20, absences=0) to trigger interventions
        # simply because the feature has high SHAP importance.
        if is_risky:
            interventions.append({
                "feature"      : feat,
                "value"        : val,
                "shap"         : round(float(shap_val), 4),
                "priority"     : rule["priority"],
                "category"     : rule["category"],
                "intervention" : rule["intervention"],
                "source"       : "rules",
            })

    interventions.sort(key=lambda x: (x["priority"], -abs(x["shap"])))
    return interventions


# ── Groq LLM Layer ────────────────────────────────────────────

def _build_prompt(student_data, rule_interventions, risk_score, risk_band) -> str:
    factors = "\n".join([
        f"  - {i['category']} ({i['feature']} = {i['value']})"
        for i in rule_interventions
    ])
    rules = "\n".join([
        f"  [{i['category']}]: {i['intervention']}"
        for i in rule_interventions
    ])
    return (
        f"You are an empathetic educational advisor helping faculty support an at-risk student.\n\n"
        f"Student situation:\n"
        f"- Risk Score: {risk_score}% ({risk_band} risk)\n"
        f"- Key concerns:\n{factors}\n\n"
        f"Suggested actions:\n{rules}\n\n"
        f"Rewrite as a single cohesive, empathetic plan for the faculty member.\n"
        f"Requirements:\n"
        f"- Warm, professional language\n"
        f"- Do NOT mention AI, scores, or model predictions\n"
        f"- No bullet points — write in short paragraphs\n"
        f"- Prioritize most urgent issues first\n"
        f"- Under 200 words\n"
        f"- Focus on what faculty should DO"
    )


def generate_llm_intervention(student_data, rule_interventions,
                               risk_score, risk_band) -> Tuple[str, str]:
    """
    Try Groq LLM to personalize intervention text.
    Falls back to rule text silently on ANY failure.
    Returns (text, source) where source is 'llm' or 'rules'.
    """
    if not rule_interventions:
        return "No critical interventions needed at this time. Continue monitoring.", "rules"

    prompt = _build_prompt(student_data, rule_interventions, risk_score, risk_band)

    for attempt, groq_model in enumerate([GROQ_MODEL, GROQ_FALLBACK]):
        try:
            if _groq_client is None:
                raise RuntimeError("Groq client not initialized")
            response = _groq_client.chat.completions.create(
                model      = groq_model,
                max_tokens = GROQ_MAX_TOKENS,
                timeout    = GROQ_TIMEOUT,
                messages   = [
                    {"role": "system", "content": "You are an empathetic educational advisor."},
                    {"role": "user",   "content": prompt},
                ]
            )
            text = response.choices[0].message.content.strip()
            if text and len(text) > 30:
                return text, "llm"
        except Exception as e:
            logger.warning(f"Groq attempt {attempt + 1} failed ({groq_model}): {type(e).__name__}")
            if attempt == 0:
                time.sleep(0.5)
            continue

    # Both attempts failed — use rule text silently
    fallback_text = " ".join([i["intervention"] for i in rule_interventions])
    return fallback_text, "rules"


# ── Full Assessment Pipeline ──────────────────────────────────

def run_full_assessment(student_id: str,
                         student_data: Dict[str, Any],
                         model,
                         explainer,
                         features: List[str],
                         threshold: float = 0.45,
                         use_llm: bool = True) -> Dict:
    """
    Full pipeline: predict → SHAP → rules → LLM (or fallback).

    Parameters:
        student_id   : identifier for the student
        student_data : dict of feature_name -> value
        model        : loaded XGBoost model
        explainer    : loaded SHAP TreeExplainer
        features     : ordered list of feature names
        threshold    : decision threshold for AT-RISK prediction
        use_llm      : if False, skip Groq entirely (saves credits in batch mode)

    Returns:
        dict with risk info, SHAP values, interventions, and narrative plan
    """
    # Step 1 — Predict
    df_input   = pd.DataFrame([student_data])[features]
    prob       = float(model.predict_proba(df_input)[0][1])
    risk_score = round(prob * 100, 1)
    risk_band  = get_risk_band(prob)
    prediction = "AT-RISK" if prob >= threshold else "PASSING"

    # Step 2 — SHAP
    sv         = explainer.shap_values(df_input)[0]
    shap_dict  = {feat: float(sv[i]) for i, feat in enumerate(features)}
    top_factors = sorted(shap_dict.items(),
                         key=lambda x: abs(x[1]), reverse=True)[:5]

    # Step 3 — Rule engine (always runs)
    rule_interventions = generate_rule_interventions(student_data, shap_dict)

    # Step 4 — LLM or rule text
    if use_llm:
        intervention_plan, plan_source = generate_llm_intervention(
            student_data, rule_interventions, risk_score, risk_band
        )
    else:
        intervention_plan = " ".join([r["intervention"] for r in rule_interventions])
        plan_source       = "rules"

    return {
        "student_id"        : student_id,
        "risk_score"        : risk_score,
        "risk_band"         : risk_band,
        "prediction"        : prediction,
        "shap_values"       : shap_dict,
        "top_factors"       : top_factors,
        "rule_interventions": rule_interventions,
        "intervention_plan" : intervention_plan,
        "plan_source"       : plan_source,
    }
