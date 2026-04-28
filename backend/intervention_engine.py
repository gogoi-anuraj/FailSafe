"""
FAILSAFE — Intervention Engine
intervention_engine.py

Imported by FastAPI backend to generate personalized
intervention plans from SHAP values and student data.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any


INTERVENTION_RULES = {
    "absences"  : {"bad_when": "high", "threshold": 6,  "priority": 1, "category": "Attendance",         "intervention": "Student has high absences. Schedule an immediate one-on-one attendance review with the class advisor. Identify whether absences are health-related, family-related, or motivational. Issue a formal attendance warning if absences exceed 10."},
    "failures"  : {"bad_when": "high", "threshold": 1,  "priority": 1, "category": "Academic History",   "intervention": "Student has a history of past failures. Assign a dedicated academic mentor for weekly check-ins. Enroll student in remedial support classes for the current subject. Set up monthly progress reviews with the HOD."},
    "G2"        : {"bad_when": "low",  "threshold": 10, "priority": 1, "category": "Academic Performance","intervention": "Student scored below passing in the second period. Provide targeted tutoring sessions before the final exam. Review second period test papers with the student to identify weak topics. Schedule bi-weekly progress checks with subject teacher."},
    "G1"        : {"bad_when": "low",  "threshold": 10, "priority": 2, "category": "Academic Performance","intervention": "Student showed early signs of struggle in the first period. Conduct an early diagnostic assessment to identify knowledge gaps. Offer access to recorded lectures and study guides. Pair with a higher-performing peer for study support."},
    "studytime" : {"bad_when": "low",  "threshold": 2,  "priority": 2, "category": "Study Habits",        "intervention": "Student reports very low weekly study time. Introduce a structured personal study timetable with the class advisor. Recommend study skills workshop offered by the institution."},
    "Dalc"      : {"bad_when": "high", "threshold": 3,  "priority": 1, "category": "Wellness",            "intervention": "Student has high weekday alcohol consumption. Refer to the student counselling or wellness center immediately. Coordinate with the student guardian if appropriate."},
    "Walc"      : {"bad_when": "high", "threshold": 3,  "priority": 2, "category": "Wellness",            "intervention": "Student has elevated weekend alcohol consumption. Suggest a confidential wellness session with a student counsellor. Monitor for associated impacts on Monday attendance."},
    "goout"     : {"bad_when": "high", "threshold": 4,  "priority": 2, "category": "Time Management",     "intervention": "Student spends significant time going out with friends. Discuss time management strategies with the class advisor. Help student create a balanced weekly schedule."},
    "health"    : {"bad_when": "low",  "threshold": 2,  "priority": 2, "category": "Health Support",      "intervention": "Student reports poor health status which may be affecting attendance. Refer to the campus health center for a wellness check. Explore whether any academic accommodations are needed."},
    "higher"    : {"bad_when": "low",  "threshold": 1,  "priority": 2, "category": "Motivation",          "intervention": "Student does not aspire to pursue higher education. Schedule a career counselling session to explore goals. Connect student with alumni or industry mentors."},
    "internet"  : {"bad_when": "low",  "threshold": 1,  "priority": 3, "category": "Resource Access",     "intervention": "Student lacks internet access at home. Ensure student is aware of on-campus Wi-Fi and computer lab resources. Provide printed study materials where possible."},
    "Medu"      : {"bad_when": "low",  "threshold": 2,  "priority": 3, "category": "Family Background",   "intervention": "Student comes from a low parental education background. Provide additional academic guidance. Connect with first-generation student support groups."},
    "Fedu"      : {"bad_when": "low",  "threshold": 2,  "priority": 3, "category": "Family Background",   "intervention": "Father has low education level. Ensure student has access to faculty office hours. Recommend peer tutoring programs."},
    "famrel"    : {"bad_when": "low",  "threshold": 2,  "priority": 2, "category": "Family & Wellbeing",  "intervention": "Student reports poor family relationship quality. Refer to a student counsellor for emotional support. Monitor for signs of stress or disengagement."},
    "schoolsup" : {"bad_when": "low",  "threshold": 1,  "priority": 2, "category": "Academic Support",    "intervention": "Student is not currently receiving any school support. Enroll in the institution academic support program. Assign a subject teacher for additional sessions."},
    "famsup"    : {"bad_when": "low",  "threshold": 1,  "priority": 3, "category": "Family Support",      "intervention": "Student lacks family educational support. Increase faculty check-ins. Share study tips and progress updates with guardians."},
    "romantic"  : {"bad_when": "high", "threshold": 1,  "priority": 3, "category": "Personal Factors",    "intervention": "Student is in a romantic relationship which may be affecting focus. Counsel sensitively on balancing personal and academic life."},
    "traveltime": {"bad_when": "high", "threshold": 3,  "priority": 3, "category": "Logistics",           "intervention": "Student has a long daily commute. Explore campus accommodation options. Consider scheduling sessions at favorable times."},
    "freetime"  : {"bad_when": "high", "threshold": 4,  "priority": 3, "category": "Time Management",     "intervention": "Student reports excessive free time indicating low engagement. Encourage joining academic clubs or project groups."},
    "paid"      : {"bad_when": "low",  "threshold": 1,  "priority": 3, "category": "Academic Support",    "intervention": "Student is not attending any paid extra classes. Recommend free tutoring or peer study groups on campus."},
    "activities": {"bad_when": "low",  "threshold": 1,  "priority": 3, "category": "Engagement",          "intervention": "Student is not involved in any extracurricular activities. Encourage joining at least one club or sport."},
}


def get_risk_band(prob: float,
                   low: float = 0.35,
                   high: float = 0.65) -> str:
    if prob >= high:
        return "HIGH"
    elif prob >= low:
        return "MEDIUM"
    return "LOW"


def generate_interventions(student_data: Dict[str, Any],
                            shap_values_dict: Dict[str, float],
                            top_n: int = 5) -> List[Dict]:
    ranked = sorted(shap_values_dict.items(),
                    key=lambda x: abs(x[1]), reverse=True)[:top_n]
    interventions = []
    for feat, shap_val in ranked:
        if feat not in INTERVENTION_RULES:
            continue
        rule     = INTERVENTION_RULES[feat]
        val      = student_data.get(feat)
        if val is None:
            continue
        bad_when  = rule["bad_when"]
        threshold = rule["threshold"]
        is_risky  = (bad_when == "high" and val >= threshold) or \
                    (bad_when == "low"  and val <  threshold)
        if is_risky or abs(shap_val) > 0.2:
            interventions.append({
                "feature"      : feat,
                "value"        : val,
                "shap"         : round(float(shap_val), 4),
                "priority"     : rule["priority"],
                "category"     : rule["category"],
                "intervention" : rule["intervention"],
            })
    interventions.sort(key=lambda x: (x["priority"], -abs(x["shap"])))
    return interventions


def run_full_assessment(student_id: str,
                         student_data: Dict[str, Any],
                         model,
                         explainer,
                         features: List[str],
                         threshold: float = 0.45) -> Dict:
    df_input   = pd.DataFrame([student_data])[features]
    prob       = float(model.predict_proba(df_input)[0][1])
    risk_score = round(prob * 100, 1)
    risk_band  = get_risk_band(prob)
    prediction = "AT-RISK" if prob >= threshold else "PASSING"
    sv         = explainer.shap_values(df_input)[0]
    shap_dict  = {feat: float(sv[i]) for i, feat in enumerate(features)}
    return {
        "student_id"   : student_id,
        "risk_score"   : risk_score,
        "risk_band"    : risk_band,
        "prediction"   : prediction,
        "shap_values"  : shap_dict,
        "interventions": generate_interventions(student_data, shap_dict),
        "top_factors"  : sorted(shap_dict.items(),
                                key=lambda x: abs(x[1]),
                                reverse=True)[:5],
    }