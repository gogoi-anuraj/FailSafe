"""
Run this once on the server to download model files from Google Drive.
python download_models.py
"""
import os
import gdown
import pathlib

BASE_DIR   = pathlib.Path(__file__).parent
MODELS_DIR = BASE_DIR / "models"
DATA_DIR   = BASE_DIR / "data" / "processed"

MODELS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Replace these with your actual Google Drive file IDs
FILES = {
    MODELS_DIR / "failsafe_model.pkl"      : "https://drive.google.com/file/d/12wblfLUzIuH5FhYhi3UbJehV9dqTYciN/view",
    MODELS_DIR / "shap_explainer.pkl"      : "https://drive.google.com/file/d/1De2w7p2quIDNsaWPba1k2fM8G8ihVLwu/view",
    MODELS_DIR / "threshold_config.json"   : "https://drive.google.com/file/d/1ZRkV-pRHnGjbXemIdivE7vUldcL44k-Q/view",
    DATA_DIR   / "features.json"           : "https://drive.google.com/file/d/1o6YfZAGBKGDvbaOx-CjJqSzZSgwp2WHN/view",
}

for path, file_id in FILES.items():
    if path.exists():
        print(f"Already exists: {path.name}")
        continue
    print(f"Downloading {path.name}...")
    gdown.download(id=file_id, output=str(path), quiet=False)
    print(f"Done: {path.name}")

print("All model files ready!")