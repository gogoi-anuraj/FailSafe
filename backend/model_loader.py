"""
FAILSAFE — Model Loader with Auto-Download
Automatically downloads model files from Google Drive if missing.
No manual steps needed after deployment.
"""

import json
import pickle
import pathlib
import logging

logger = logging.getLogger("failsafe.model_loader")

BASE_DIR   = pathlib.Path(__file__).parent
MODELS_DIR = BASE_DIR / "models"
DATA_DIR   = BASE_DIR / "data" / "processed"

# ── Replace these with your actual Google Drive file IDs ──────
# GDRIVE_FILES = {
#     MODELS_DIR / "failsafe_model.pkl"    : "https://drive.google.com/file/d/12wblfLUzIuH5FhYhi3UbJehV9dqTYciN/view",
#     MODELS_DIR / "shap_explainer.pkl"    : "https://drive.google.com/file/d/1De2w7p2quIDNsaWPba1k2fM8G8ihVLwu/view",
#     MODELS_DIR / "threshold_config.json" : "https://drive.google.com/file/d/1ZRkV-pRHnGjbXemIdivE7vUldcL44k-Q/view",
#     DATA_DIR   / "features.json"         : "https://drive.google.com/file/d/1o6YfZAGBKGDvbaOx-CjJqSzZSgwp2WHN/view",
# }

# Global model references — None until loaded
MODEL              = None
EXPLAINER          = None
THRESH_CONFIG      = None
FEATURES           = None
DECISION_THRESHOLD = 0.45
_loaded            = False


def _ensure_dirs():
    """Create model and data directories if they don't exist."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)


# def _download_from_gdrive():
#     """
#     Download missing files from Google Drive using gdown.
#     Skips files that already exist.
#     Skips files whose ID is still the placeholder.
#     """
#     try:
#         import gdown
#     except ImportError:
#         logger.warning("gdown not installed — skipping auto-download. "
#                        "Run: pip install gdown")
#         return

#     for path, file_id in GDRIVE_FILES.items():
#         if path.exists():
#             logger.info(f"Already exists: {path.name}")
#             continue

#         if file_id.startswith("YOUR_"):
#             logger.warning(f"No Google Drive ID set for {path.name} — skipping.")
#             continue

        # logger.info(f"Downloading {path.name} from Google Drive...")
        # try:
        #     url = f"https://drive.google.com/uc?id={file_id}"
        #     gdown.download(url, str(path), quiet=False)
        #     if path.exists():
        #         logger.info(f"Downloaded: {path.name} ({path.stat().st_size // 1024} KB)")
        #     else:
        #         logger.error(f"Download failed silently: {path.name}")
        # except Exception as e:
        #     logger.error(f"Failed to download {path.name}: {e}")


def _check_missing():
    required_files = [
        MODELS_DIR / "failsafe_model.pkl",
        MODELS_DIR / "shap_explainer.pkl",
        MODELS_DIR / "threshold_config.json",
        DATA_DIR   / "features.json",
    ]

    missing = [str(p) for p in required_files if not p.exists()]
    return missing


def load_models():
    global MODEL, EXPLAINER, THRESH_CONFIG, FEATURES, DECISION_THRESHOLD, _loaded

    if _loaded:
        return

    _ensure_dirs()

    # Check files exist
    missing = _check_missing()
    if missing:
        raise RuntimeError(f"Missing model files: {missing}")

    logger.info("Loading model files...")

    with open(MODELS_DIR / "failsafe_model.pkl", "rb") as f:
        MODEL = pickle.load(f)

    with open(MODELS_DIR / "shap_explainer.pkl", "rb") as f:
        EXPLAINER = pickle.load(f)

    with open(MODELS_DIR / "threshold_config.json") as f:
        THRESH_CONFIG = json.load(f)
        DECISION_THRESHOLD = THRESH_CONFIG["decision_threshold"]

    with open(DATA_DIR / "features.json") as f:
        FEATURES = json.load(f)

    _loaded = True

    logger.info(
        f"Models loaded — {len(FEATURES)} features | threshold={DECISION_THRESHOLD}"
    )