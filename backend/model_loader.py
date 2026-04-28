"""
FAILSAFE — Model Loader
Loads XGBoost model, SHAP explainer, feature list, and threshold
config once at app startup. All routes import from here.
"""

import json
import pickle
import pathlib

# ── Paths ─────────────────────────────────────────────────────
BASE_DIR    = pathlib.Path(__file__).parent
MODELS_DIR  = BASE_DIR / "models"
DATA_DIR    = BASE_DIR / "data" / "processed"


def _load():
    with open(MODELS_DIR / "failsafe_model.pkl", "rb") as f:
        model = pickle.load(f)

    with open(MODELS_DIR / "shap_explainer.pkl", "rb") as f:
        explainer = pickle.load(f)

    with open(MODELS_DIR / "threshold_config.json") as f:
        thresh = json.load(f)

    with open(DATA_DIR / "features.json") as f:
        features = json.load(f)

    return model, explainer, thresh, features


# Load once at import time
try:
    MODEL, EXPLAINER, THRESH_CONFIG, FEATURES = _load()
    DECISION_THRESHOLD = THRESH_CONFIG["decision_threshold"]
    print(f"Model loaded — {len(FEATURES)} features | threshold={DECISION_THRESHOLD}")
except Exception as e:
    raise RuntimeError(f"Failed to load model artifacts: {e}")
