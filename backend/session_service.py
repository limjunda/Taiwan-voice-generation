import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel

SESSIONS_DIR = Path("sessions")
SESSIONS_DIR.mkdir(exist_ok=True)

class Session(BaseModel):
    id: str
    created_at: str
    name: str
    persona_id: Optional[str]
    text_type: str
    text_content: str
    voices_tested: List[str]
    favorites: List[str]
    generated_files: List[str]

def create_session(
    name: str,
    persona_id: str | None,
    text_type: str,
    text_content: str,
    voices: List[str],
    files: List[str]
) -> Session:
    timestamp = datetime.now()
    session = Session(
        id=f"session_{timestamp.strftime('%Y-%m-%d_%H%M%S')}",
        created_at=timestamp.isoformat(),
        name=name,
        persona_id=persona_id,
        text_type=text_type,
        text_content=text_content,
        voices_tested=voices,
        favorites=[],
        generated_files=files
    )
    save_session(session)
    return session

def save_session(session: Session):
    path = SESSIONS_DIR / f"{session.id}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(session.model_dump(), f, ensure_ascii=False, indent=2)

def list_sessions() -> List[Session]:
    sessions = []
    for path in sorted(SESSIONS_DIR.glob("*.json"), reverse=True):
        with open(path, encoding="utf-8") as f:
            sessions.append(Session(**json.load(f)))
    return sessions

def get_session(session_id: str) -> Optional[Session]:
    path = SESSIONS_DIR / f"{session_id}.json"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return Session(**json.load(f))
    return None

def update_favorites(session_id: str, favorites: List[str]) -> Optional[Session]:
    session = get_session(session_id)
    if session:
        session.favorites = favorites
        save_session(session)
    return session
