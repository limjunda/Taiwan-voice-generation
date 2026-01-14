"""
Script to migrate legacy metadata files to the new format.
Run this from the backend directory: python migrate_legacy_metadata.py
"""

import os
from pathlib import Path

OUTPUT_DIR = Path("output")

# Mapping of persona slugs to full data
PERSONA_DATA = {
    "default": {
        "persona_id": "none",
        "persona_name": "default",
        "local_name": "",
        "archetype": "",
        "traits": "",
        "tone_instructions": "",
        "recommended_voice": "",
        "is_custom": False
    },
    "Skeptical_Auntie": {
        "persona_id": "skeptical_auntie",
        "persona_name": "Skeptical Auntie",
        "local_name": "Fang Bei",
        "archetype": "Scammer-Aware",
        "traits": "Suspicious, thinks you are a fraud",
        "tone_instructions": "Suspicious, sharp tone. Questioning intonation. Lower pitch, guarded.",
        "recommended_voice": "Orus",
        "is_custom": False
    },
    "Busy_Boss": {
        "persona_id": "busy_boss",
        "persona_name": "Busy Boss",
        "local_name": "Mang",
        "archetype": "SME Owner",
        "traits": "Impatient, abrupt, rushing",
        "tone_instructions": "Fast pace, annoyed tone. Interrupts often. Uses short sentences. Sounds distracted.",
        "recommended_voice": "Fenrir",
        "is_custom": False
    },
    "Apathetic_Lead": {
        "persona_id": "apathetic_lead",
        "persona_name": "Apathetic Lead",
        "local_name": "Sui Bian",
        "archetype": "Whatever Guy",
        "traits": "Low energy, non-committal",
        "tone_instructions": "Monotone, bored, low energy. Sounds tired. Long pauses between words.",
        "recommended_voice": "Umbriel",
        "is_custom": False
    },
    "Polite_Rejector": {
        "persona_id": "polite_rejector",
        "persona_name": "Polite Rejector",
        "local_name": "Pai-Se",
        "archetype": "Soft Rejector",
        "traits": "Very polite but firm non-buyer",
        "tone_instructions": "Soft, apologetic, slow pace. Gentle but refuses to engage. High pitch, breathy voice.",
        "recommended_voice": "Leda",
        "is_custom": False
    },
    "Chatty_Elder": {
        "persona_id": "chatty_elder",
        "persona_name": "Chatty Elder",
        "local_name": "Gong Wei",
        "archetype": "Lonely Senior",
        "traits": "Friendly but off-topic",
        "tone_instructions": "Warm, enthusiastic, slightly slower pace. Laughs while talking. Sounds like an older person.",
        "recommended_voice": "Sulafat",
        "is_custom": False
    }
}


def parse_legacy_metadata(filepath: Path) -> dict:
    """Parse old format metadata file."""
    data = {}
    with open(filepath, encoding="utf-8") as f:
        for line in f:
            if ":" in line:
                key, value = line.split(":", 1)
                data[key.strip()] = value.strip()
    return data


def get_persona_slug_from_filename(filename: str) -> str:
    """Extract persona slug from filename like 2026-01-14_012241_Zephyr_default.txt"""
    parts = filename.replace(".txt", "").split("_")
    if len(parts) >= 4:
        return "_".join(parts[3:])
    return "default"


def create_new_metadata(old_data: dict, persona_slug: str) -> str:
    """Create new format metadata content."""
    persona_info = PERSONA_DATA.get(persona_slug, PERSONA_DATA["default"])
    
    lines = [
        f"voice: {old_data.get('voice', 'unknown')}",
        f"persona_id: {persona_info['persona_id']}",
        f"persona_name: {persona_info['persona_name']}",
        f"local_name: {persona_info['local_name']}",
        f"archetype: {persona_info['archetype']}",
        f"traits: {persona_info['traits']}",
        f"tone_instructions: {persona_info['tone_instructions']}",
        f"recommended_voice: {persona_info['recommended_voice']}",
        f"is_custom: {persona_info['is_custom']}",
        f"model: {old_data.get('model', 'gemini-2.5-flash-preview-tts')}",
        f"text: {old_data.get('text', '')}",
        f"generated_at: {old_data.get('generated_at', '')}"
    ]
    
    return "\n".join(lines)


def migrate_metadata_files():
    """Migrate all legacy metadata files in the output directory."""
    if not OUTPUT_DIR.exists():
        print(f"Output directory not found: {OUTPUT_DIR}")
        return
    
    txt_files = list(OUTPUT_DIR.glob("*.txt"))
    migrated = 0
    
    for txt_file in txt_files:
        if txt_file.name == "favorites.json":
            continue
            
        print(f"Processing: {txt_file.name}")
        
        # Read old format
        old_data = parse_legacy_metadata(txt_file)
        
        # Check if already in new format
        if "persona_id" in old_data and "persona_name" in old_data:
            print(f"  Already migrated, skipping")
            continue
        
        # Get persona slug from filename
        persona_slug = get_persona_slug_from_filename(txt_file.name)
        print(f"  Persona slug: {persona_slug}")
        
        # Create new format
        new_content = create_new_metadata(old_data, persona_slug)
        
        # Write back
        with open(txt_file, "w", encoding="utf-8") as f:
            f.write(new_content)
        
        print(f"  Migrated!")
        migrated += 1
    
    print(f"\nDone! Migrated {migrated} files.")


if __name__ == "__main__":
    migrate_metadata_files()
