from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, PlainTextResponse
from typing import List, Optional
from pathlib import Path
from pydantic import BaseModel as PydanticBaseModel

from auth import validate_credentials
from tts_service import generate_speech, generate_batch
from models import GenerateRequest, GenerateResponse, BatchRequest
from session_service import (
    list_sessions, get_session, update_favorites, create_session, save_session,
    get_active_session_id, set_active_session, list_session_audio, get_session_folder,
    SESSIONS_DIR
)
from data_manager import (
    load_custom_personas, save_custom_persona, delete_custom_persona, get_all_personas
)

app = FastAPI(title="Taiwan Voice Generator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Legacy output folder
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

@app.on_event("startup")
async def startup():
    result = validate_credentials()
    if not result["valid"]:
        print(f"Warning: {result.get('error', 'Unknown error')}")
    else:
        print(f"Auth: {result['method']}")

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/auth/status")
async def auth_status():
    return validate_credentials()

# ==================== GENERATE ====================

@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    session_id = get_active_session_id()
    return await generate_speech(request, session_id)

@app.post("/batch")
async def batch_generate(request: BatchRequest):
    session_id = get_active_session_id()
    results = await generate_batch(
        request.voices,
        request.text,
        request.persona_id,
        request.model.value,
        session_id
    )
    return {"results": results, "total": len(results)}

# ==================== AUDIO ====================

def get_audio_folder(session_id: Optional[str] = None) -> Path:
    """Get the audio folder (session or legacy)."""
    if session_id:
        return get_session_folder(session_id)
    active = get_active_session_id()
    if active:
        return get_session_folder(active)
    return OUTPUT_DIR

@app.get("/audio")
async def list_audio(session_id: Optional[str] = None, legacy: bool = False):
    """List audio files. If session_id is provided, list from that session. If legacy=true, list from legacy output folder."""
    import json
    
    # Determine which folder to use
    if legacy:
        folder = OUTPUT_DIR
    elif session_id:
        folder = get_session_folder(session_id)
    else:
        active = get_active_session_id()
        if active:
            folder = get_session_folder(active)
        else:
            folder = OUTPUT_DIR
    
    favorites_file = folder / "favorites.json"
    favorites = []
    if favorites_file.exists():
        with open(favorites_file, encoding="utf-8") as f:
            favorites = json.load(f)
    
    audio_files = []
    for wav_file in sorted(folder.glob("*.wav"), reverse=True):
        meta_file = folder / (wav_file.stem + ".txt")
        voice = "unknown"
        persona = "default"
        timestamp = ""
        
        if meta_file.exists():
            with open(meta_file, encoding="utf-8") as f:
                for line in f:
                    if line.startswith("voice:"):
                        voice = line.split(":", 1)[1].strip()
                    elif line.startswith("persona_name:"):
                        persona = line.split(":", 1)[1].strip()
                    elif line.startswith("generated_at:"):
                        timestamp = line.split(":", 1)[1].strip()
        else:
            name = wav_file.stem
            parts = name.split("_")
            if len(parts) >= 3:
                timestamp = f"{parts[0]}_{parts[1]}"
                voice = parts[2] if len(parts) > 2 else "unknown"
                persona = "_".join(parts[3:]) if len(parts) > 3 else "default"
        
        audio_files.append({
            "filename": wav_file.name,
            "voice": voice,
            "persona": persona,
            "timestamp": timestamp,
            "size_bytes": wav_file.stat().st_size,
            "is_favorite": wav_file.name in favorites,
            "session_id": session_id or get_active_session_id()
        })
    return audio_files

@app.get("/audio/all")
async def list_all_audio():
    """List all audio files from all sessions and legacy folder."""
    import json
    all_files = []
    
    # Legacy folder
    for wav_file in OUTPUT_DIR.glob("*.wav"):
        all_files.append({
            "filename": wav_file.name,
            "folder": "legacy",
            "session_id": None
        })
    
    # Session folders
    for session_dir in SESSIONS_DIR.iterdir():
        if session_dir.is_dir():
            for wav_file in session_dir.glob("*.wav"):
                all_files.append({
                    "filename": wav_file.name,
                    "folder": session_dir.name,
                    "session_id": session_dir.name
                })
    
    return all_files

@app.get("/audio/{filename}")
async def serve_audio(filename: str, session_id: Optional[str] = None):
    """Serve an audio file."""
    folder = get_audio_folder(session_id)
    file_path = folder / filename
    
    # Also check legacy folder
    if not file_path.exists():
        file_path = OUTPUT_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(file_path, media_type="audio/wav")

@app.get("/metadata/{filename}")
async def serve_metadata(filename: str, session_id: Optional[str] = None):
    """Serve a metadata .txt file."""
    folder = get_audio_folder(session_id)
    file_path = folder / filename
    
    if not file_path.exists():
        file_path = OUTPUT_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Metadata file not found")
    with open(file_path, encoding="utf-8") as f:
        return PlainTextResponse(f.read())

# ==================== FAVORITES ====================

@app.get("/favorites")
async def list_favorites():
    """List favorited audio files."""
    import json
    folder = get_audio_folder()
    favorites_file = folder / "favorites.json"
    if not favorites_file.exists():
        return []
    
    with open(favorites_file, encoding="utf-8") as f:
        favorites = json.load(f)
    
    all_audio = await list_audio()
    return [a for a in all_audio if a["is_favorite"]]

@app.post("/favorites/{filename}")
async def add_favorite(filename: str):
    """Add an audio file to favorites."""
    import json
    folder = get_audio_folder()
    favorites_file = folder / "favorites.json"
    favorites = []
    if favorites_file.exists():
        with open(favorites_file, encoding="utf-8") as f:
            favorites = json.load(f)
    
    if filename not in favorites:
        favorites.append(filename)
        with open(favorites_file, "w", encoding="utf-8") as f:
            json.dump(favorites, f)
    return {"success": True, "favorites": favorites}

@app.delete("/favorites/{filename}")
async def remove_favorite(filename: str):
    """Remove an audio file from favorites."""
    import json
    folder = get_audio_folder()
    favorites_file = folder / "favorites.json"
    favorites = []
    if favorites_file.exists():
        with open(favorites_file, encoding="utf-8") as f:
            favorites = json.load(f)
    
    if filename in favorites:
        favorites.remove(filename)
        with open(favorites_file, "w", encoding="utf-8") as f:
            json.dump(favorites, f)
    return {"success": True, "favorites": favorites}

# ==================== SESSIONS ====================

class CreateSessionRequest(PydanticBaseModel):
    name: str
    persona_id: Optional[str] = None
    text_type: str = "demo"
    text_content: str = ""

class UpdateSessionRequest(PydanticBaseModel):
    voices: Optional[List[str]] = None
    files: Optional[List[str]] = None

@app.get("/sessions")
async def get_sessions():
    sessions = list_sessions()
    active = get_active_session_id()
    return {
        "sessions": [s.model_dump() for s in sessions],
        "active_session_id": active
    }

@app.get("/sessions/active")
async def get_active_session():
    """Get the currently active session."""
    active = get_active_session_id()
    if active:
        session = get_session(active)
        return {"session": session.model_dump() if session else None, "id": active}
    return {"session": None, "id": None}

@app.post("/sessions/active/{session_id}")
async def activate_session(session_id: str):
    """Set the active session."""
    session = set_active_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"success": True, "session": session.model_dump()}

@app.get("/sessions/{session_id}")
async def get_session_by_id(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@app.post("/sessions")
async def create_new_session(request: CreateSessionRequest):
    session = create_session(
        name=request.name,
        persona_id=request.persona_id,
        text_type=request.text_type,
        text_content=request.text_content
    )
    return {"session": session.model_dump(), "id": session.id}

@app.patch("/sessions/{session_id}")
async def update_session(session_id: str, request: UpdateSessionRequest):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if request.voices:
        session.voices_tested.extend(request.voices)
    if request.files:
        session.generated_files.extend(request.files)
    
    save_session(session)
    return session

@app.patch("/sessions/{session_id}/favorites")
async def update_session_favorites(session_id: str, favorites: List[str]):
    session = update_favorites(session_id, favorites)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@app.get("/sessions/{session_id}/audio")
async def get_session_audio(session_id: str):
    """Get audio files for a specific session."""
    return list_session_audio(session_id)

# ==================== CUSTOM PERSONAS ====================

class CustomPersonaRequest(PydanticBaseModel):
    id: Optional[str] = None
    name: str
    local_name: str = ""
    archetype: str = ""
    traits: str = ""
    tone_instructions: str
    recommended_voice: str = ""

@app.get("/custom-personas")
async def get_custom_personas():
    """List all custom personas."""
    return load_custom_personas()

@app.get("/personas/all")
async def get_all_personas_endpoint():
    """Get all personas (built-in + custom)."""
    return get_all_personas()

@app.post("/custom-personas")
async def create_custom_persona(request: CustomPersonaRequest):
    """Create a new custom persona."""
    persona = save_custom_persona(request.model_dump())
    return {"success": True, "persona": persona}

@app.put("/custom-personas/{persona_id}")
async def update_custom_persona(persona_id: str, request: CustomPersonaRequest):
    """Update an existing custom persona."""
    persona_data = request.model_dump()
    persona_data["id"] = persona_id
    persona = save_custom_persona(persona_data)
    return {"success": True, "persona": persona}

@app.delete("/custom-personas/{persona_id}")
async def delete_custom_persona_endpoint(persona_id: str):
    """Delete a custom persona."""
    success = delete_custom_persona(persona_id)
    if not success:
        raise HTTPException(status_code=404, detail="Custom persona not found")
    return {"success": True}

# Serve frontend static files (must be last)
app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")
