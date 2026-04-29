# scripts/download_models.py
"""
Script to download required AI models for EduVerify
"""
import os
import requests
from pathlib import Path

MODELS_DIR = Path("models")
MODELS_DIR.mkdir(exist_ok=True)

MODELS = {
    "yolov8n-face.pt": "https://github.com/akanametov/yolov8-face/releases/download/v0.0.0/yolov8n-face.pt",
    "buffalo_l.zip": "https://github.com/deepinsight/insightface/releases/download/v0.7/buffalo_l.zip",
}

def download_model(name: str, url: str):
    """Download model file"""
    filepath = MODELS_DIR / name
    if filepath.exists():
        print(f"Model {name} already exists, skipping...")
        return
    
    print(f"Downloading {name}...")
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    with open(filepath, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    print(f"Downloaded {name}")

if __name__ == "__main__":
    print("Downloading AI models...")
    for name, url in MODELS.items():
        download_model(name, url)
    print("All models downloaded successfully!")