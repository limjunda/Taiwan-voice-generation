import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel

# Sessions are stored in output/sessions/{session_id}/
OUTPUT_DIR = Path("output")
SESSIONS_DIR = OUTPUT_DIR / "sessions"
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

# Track active session
_active_session_id: Optional[str] = None

class Session(BaseModel):
    id: str
    created_at: str
    name: str
    persona_id: Optional[str] = None
    text_type: str = "demo"
    text_content: str = ""
    voices_tested: List[str] = []
    favorites: List[str] = []
    generated_files: List[str] = []

def get_session_folder(session_id: str) -> Path:
    """Get the folder path for a session."""
    folder = SESSIONS_DIR / session_id
    folder.mkdir(parents=True, exist_ok=True)
    return folder

def create_session(
    name: str,
    persona_id: str | None = None,
    text_type: str = "demo",
    text_content: str = "",
    voices: List[str] = None,
    files: List[str] = None
) -> Session:
    """Create a new session with its own folder."""
    global _active_session_id
    
    timestamp = datetime.now()
    session_id = f"session_{timestamp.strftime('%Y-%m-%d_%H%M%S')}"
    
    # Create session folder
    session_folder = get_session_folder(session_id)
    
    session = Session(
        id=session_id,
        created_at=timestamp.isoformat(),
        name=name,
        persona_id=persona_id,
        text_type=text_type,
        text_content=text_content,
        voices_tested=voices or [],
        favorites=[],
        generated_files=files or []
    )
    
    save_session(session)
    _active_session_id = session_id
    
    return session

def save_session(session: Session):
    """Save session metadata to its folder."""
    session_folder = get_session_folder(session.id)
    path = session_folder / "session.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(session.model_dump(), f, ensure_ascii=False, indent=2)

def list_sessions() -> List[Session]:
    """List all sessions."""
    sessions = []
    for folder in sorted(SESSIONS_DIR.iterdir(), reverse=True):
        if folder.is_dir():
            session_file = folder / "session.json"
            if session_file.exists():
                with open(session_file, encoding="utf-8") as f:
                    sessions.append(Session(**json.load(f)))
    return sessions

def get_session(session_id: str) -> Optional[Session]:
    """Get a session by ID."""
    session_folder = SESSIONS_DIR / session_id
    session_file = session_folder / "session.json"
    if session_file.exists():
        with open(session_file, encoding="utf-8") as f:
            return Session(**json.load(f))
    return None

def get_active_session() -> Optional[Session]:
    """Get the currently active session."""
    global _active_session_id
    if _active_session_id:
        return get_session(_active_session_id)
    return None

def get_active_session_id() -> Optional[str]:
    """Get the ID of the currently active session."""
    return _active_session_id

def set_active_session(session_id: str) -> Optional[Session]:
    """Set the active session."""
    global _active_session_id
    session = get_session(session_id)
    if session:
        _active_session_id = session_id
        return session
    return None

def add_file_to_session(session_id: str, filename: str, voice: str) -> Optional[Session]:
    """Add a generated file to a session."""
    session = get_session(session_id)
    if session:
        if filename not in session.generated_files:
            session.generated_files.append(filename)
        if voice not in session.voices_tested:
            session.voices_tested.append(voice)
        save_session(session)
        return session
    return None

def update_favorites(session_id: str, favorites: List[str]) -> Optional[Session]:
    """Update favorites for a session."""
    session = get_session(session_id)
    if session:
        session.favorites = favorites
        save_session(session)
    return session

def list_session_audio(session_id: str) -> List[dict]:
    """List all audio files in a session folder."""
    session_folder = SESSIONS_DIR / session_id
    audio_files = []
    
    if not session_folder.exists():
        return audio_files
    
    for wav_file in sorted(session_folder.glob("*.wav"), reverse=True):
        meta_file = session_folder / (wav_file.stem + ".txt")
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
        
        audio_files.append({
            "filename": wav_file.name,
            "voice": voice,
            "persona": persona,
            "timestamp": timestamp,
            "size_bytes": wav_file.stat().st_size,
            "session_id": session_id
        })
    
    return audio_files
