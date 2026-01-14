import json
from pathlib import Path
from typing import Optional

DATA_DIR = Path("../data")

def load_voices(data_dir: Path = DATA_DIR) -> list:
    with open(data_dir / "voices.json", encoding="utf-8") as f:
        return json.load(f)["voices"]

def load_personas(data_dir: Path = DATA_DIR) -> dict:
    with open(data_dir / "personas.json", encoding="utf-8") as f:
        data = json.load(f)["personas"]
        return {p["id"]: p for p in data}

def load_demo_texts(data_dir: Path = DATA_DIR) -> dict:
    with open(data_dir / "demo_texts.json", encoding="utf-8") as f:
        return json.load(f)

# Custom Personas

CUSTOM_PERSONAS_FILE = DATA_DIR / "custom_personas.json"

def load_custom_personas() -> dict:
    """Load user-created custom personas."""
    if not CUSTOM_PERSONAS_FILE.exists():
        return {}
    
    with open(CUSTOM_PERSONAS_FILE, encoding="utf-8") as f:
        data = json.load(f)
        personas = data.get("personas", [])
        # Mark as custom
        for p in personas:
            p["is_custom"] = True
        return {p["id"]: p for p in personas}

def save_custom_persona(persona: dict) -> dict:
    """Save a custom persona."""
    # Load existing
    if CUSTOM_PERSONAS_FILE.exists():
        with open(CUSTOM_PERSONAS_FILE, encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {"personas": []}
    
    # Generate ID if not provided
    if "id" not in persona or not persona["id"]:
        persona["id"] = f"custom_{persona.get('name', 'persona').lower().replace(' ', '_')}"
    
    persona["is_custom"] = True
    
    # Update or add
    existing_ids = [p["id"] for p in data["personas"]]
    if persona["id"] in existing_ids:
        # Update existing
        for i, p in enumerate(data["personas"]):
            if p["id"] == persona["id"]:
                data["personas"][i] = persona
                break
    else:
        # Add new
        data["personas"].append(persona)
    
    # Save
    with open(CUSTOM_PERSONAS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return persona

def delete_custom_persona(persona_id: str) -> bool:
    """Delete a custom persona by ID."""
    if not CUSTOM_PERSONAS_FILE.exists():
        return False
    
    with open(CUSTOM_PERSONAS_FILE, encoding="utf-8") as f:
        data = json.load(f)
    
    original_count = len(data["personas"])
    data["personas"] = [p for p in data["personas"] if p["id"] != persona_id]
    
    if len(data["personas"]) < original_count:
        with open(CUSTOM_PERSONAS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    
    return False

def get_all_personas() -> dict:
    """Get both built-in and custom personas."""
    personas = load_personas()
    custom = load_custom_personas()
    personas.update(custom)
    return personas
