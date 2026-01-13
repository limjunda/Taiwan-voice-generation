import json
from pathlib import Path

def load_voices(data_dir: Path = Path("../data")) -> list:
    with open(data_dir / "voices.json", encoding="utf-8") as f:
        return json.load(f)["voices"]

def load_personas(data_dir: Path = Path("../data")) -> dict:
    with open(data_dir / "personas.json", encoding="utf-8") as f:
        data = json.load(f)["personas"]
        return {p["id"]: p for p in data}

def load_demo_texts(data_dir: Path = Path("../data")) -> dict:
    with open(data_dir / "demo_texts.json", encoding="utf-8") as f:
        return json.load(f)
