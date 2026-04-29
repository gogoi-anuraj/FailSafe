"""
FAILSAFE — Model Loader
Loads XGBoost model, SHAP explainer, feature list, and threshold
config once at app startup. All routes import from here.
"""

import json
import pickle
import pathlib

# ── Paths ─────────────────────────────────────────────────────
BASE_DIR   = pathlib.Path(__file__).parent
MODELS_DIR = BASE_DIR / "models"
DATA_DIR   = BASE_DIR / "data" / "processed"

def _download_if_missing():
    """Download model files from Google Drive if not present."""
    try:
        import gdown
    except ImportError:
        return  # gdown not installed, skip

    MODELS_DIR.mkdir(exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    FILES = {
        MODELS_DIR / "failsafe_model.pkl"    : "https://drive.google.com/file/d/12wblfLUzIuH5FhYhi3UbJehV9dqTYciN/view",
        MODELS_DIR / "shap_explainer.pkl"    : "https://drive.google.com/file/d/1De2w7p2quIDNsaWPba1k2fM8G8ihVLwu/view",
        MODELS_DIR / "threshold_config.json" : "https://drive.google.com/file/d/1ZRkV-pRHnGjbXemIdivE7vUldcL44k-Q/view",
        DATA_DIR   / "features.json"         : "https://drive.google.com/file/d/1o6YfZAGBKGDvbaOx-CjJqSzZSgwp2WHN/view",
    }

    for path, file_id in FILES.items():
        if not path.exists():
            print(f"Downloading {path.name} from Google Drive...")
            gdown.download(id=file_id, output=str(path), quiet=False)


def _load():
    # Clear error messages if files are missing
    missing = []
    for f in ["failsafe_model.pkl", "shap_explainer.pkl", "threshold_config.json"]:
        if not (MODELS_DIR / f).exists():
            missing.append(f"models/{f}")
    if not (DATA_DIR / "features.json").exists():
        missing.append("data/processed/features.json")

    if missing:
        raise RuntimeError(
            f"Missing model files: {missing}\n"
            "Upload these files to the backend/models/ and "
            "backend/data/processed/ directories before starting the server."
        )

    with open(MODELS_DIR / "failsafe_model.pkl", "rb") as f:
        model = pickle.load(f)

    with open(MODELS_DIR / "shap_explainer.pkl", "rb") as f:
        explainer = pickle.load(f)

    with open(MODELS_DIR / "threshold_config.json") as f:
        thresh = json.load(f)

    with open(DATA_DIR / "features.json") as f:
        features = json.load(f)

    return model, explainer, thresh, features

_download_if_missing()
# Load once at import time
try:
    MODEL, EXPLAINER, THRESH_CONFIG, FEATURES = _load()
    DECISION_THRESHOLD = THRESH_CONFIG["decision_threshold"]
    print(f"Model loaded — {len(FEATURES)} features | threshold={DECISION_THRESHOLD}")
except RuntimeError as e:
    raise RuntimeError(str(e))
except Exception as e:
    raise RuntimeError(f"Failed to load model artifacts: {e}")
