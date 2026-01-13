from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import List
from auth import validate_credentials
from tts_service import generate_speech, generate_batch
from models import GenerateRequest, GenerateResponse, BatchRequest
from session_service import list_sessions, get_session, update_favorites

app = FastAPI(title="Taiwan Voice Generator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    return await generate_speech(request)

@app.post("/batch")
async def batch_generate(request: BatchRequest):
    results = await generate_batch(
        request.voices,
        request.text,
        request.persona_id,
        request.model
    )
    return {"results": results, "total": len(results)}

from pathlib import Path
from session_service import create_session

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

@app.get("/audio")
async def list_audio():
    """List all generated audio files with their metadata."""
    audio_files = []
    favorites_file = OUTPUT_DIR / "favorites.json"
    favorites = []
    if favorites_file.exists():
        import json
        with open(favorites_file, encoding="utf-8") as f:
            favorites = json.load(f)
    
    for wav_file in sorted(OUTPUT_DIR.glob("*.wav"), reverse=True):
        # Try to read metadata from .txt file
        meta_file = OUTPUT_DIR / (wav_file.stem + ".txt")
        voice = "unknown"
        persona = "default"
        timestamp = ""
        
        if meta_file.exists():
            with open(meta_file, encoding="utf-8") as f:
                for line in f:
                    if line.startswith("voice:"):
                        voice = line.split(":", 1)[1].strip()
                    elif line.startswith("persona:"):
                        persona = line.split(":", 1)[1].strip()
                    elif line.startswith("generated_at:"):
                        timestamp = line.split(":", 1)[1].strip()
        else:
            # Fallback: parse from filename (2026-01-14_014410_Voice_Persona.wav)
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
            "is_favorite": wav_file.name in favorites
        })
    return audio_files

@app.get("/favorites")
async def list_favorites():
    """List favorited audio files."""
    import json
    favorites_file = OUTPUT_DIR / "favorites.json"
    if not favorites_file.exists():
        return []
    
    with open(favorites_file, encoding="utf-8") as f:
        favorites = json.load(f)
    
    # Return full audio info for favorites
    all_audio = await list_audio()
    return [a for a in all_audio if a["is_favorite"]]

@app.post("/favorites/{filename}")
async def add_favorite(filename: str):
    """Add an audio file to favorites."""
    import json
    favorites_file = OUTPUT_DIR / "favorites.json"
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
    favorites_file = OUTPUT_DIR / "favorites.json"
    favorites = []
    if favorites_file.exists():
        with open(favorites_file, encoding="utf-8") as f:
            favorites = json.load(f)
    
    if filename in favorites:
        favorites.remove(filename)
        with open(favorites_file, "w", encoding="utf-8") as f:
            json.dump(favorites, f)
    return {"success": True, "favorites": favorites}

@app.get("/audio/{filename}")
async def serve_audio(filename: str):
    """Serve audio files from output directory."""
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(file_path, media_type="audio/wav")

@app.get("/metadata/{filename}")
async def serve_metadata(filename: str):
    """Serve metadata .txt files."""
    from fastapi.responses import PlainTextResponse
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Metadata file not found")
    with open(file_path, encoding="utf-8") as f:
        return PlainTextResponse(f.read())

@app.get("/sessions")
async def get_sessions():
    return list_sessions()

@app.get("/sessions/{session_id}")
async def get_session_by_id(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

from pydantic import BaseModel as PydanticBaseModel
from typing import Optional

class CreateSessionRequest(PydanticBaseModel):
    name: str
    persona_id: Optional[str] = None
    text_type: str
    text_content: str
    voices: List[str]
    files: List[str]

class UpdateSessionRequest(PydanticBaseModel):
    voices: Optional[List[str]] = None
    files: Optional[List[str]] = None

@app.post("/sessions")
async def create_new_session(request: CreateSessionRequest):
    session = create_session(
        name=request.name,
        persona_id=request.persona_id,
        text_type=request.text_type,
        text_content=request.text_content,
        voices=request.voices,
        files=request.files
    )
    return session

@app.patch("/sessions/{session_id}")
async def update_session(session_id: str, request: UpdateSessionRequest):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Update voices and files
    if request.voices:
        session.voices_tested.extend(request.voices)
    if request.files:
        session.generated_files.extend(request.files)
    
    # Save updated session
    from session_service import save_session
    save_session(session)
    return session

@app.patch("/sessions/{session_id}/favorites")
async def update_session_favorites(session_id: str, favorites: List[str]):
    session = update_favorites(session_id, favorites)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

# Serve frontend static files (must be last)
app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")
