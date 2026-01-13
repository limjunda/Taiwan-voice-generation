import pytest
from pathlib import Path
from session_service import create_session, list_sessions, get_session, update_favorites, SESSIONS_DIR

def test_create_and_list_sessions(tmp_path, monkeypatch):
    # Patch SESSIONS_DIR to use temp directory
    monkeypatch.setattr("session_service.SESSIONS_DIR", tmp_path)
    
    # Create a session
    session = create_session(
        name="Test Session",
        persona_id="busy_boss",
        text_type="demo",
        text_content="Hello",
        voices=["Zephyr", "Puck"],
        files=["file1.wav", "file2.wav"]
    )
    
    assert session.name == "Test Session"
    assert session.voices_tested == ["Zephyr", "Puck"]
    
    # List sessions
    sessions = list_sessions()
    assert len(sessions) == 1
    assert sessions[0].id == session.id

def test_get_session(tmp_path, monkeypatch):
    monkeypatch.setattr("session_service.SESSIONS_DIR", tmp_path)
    
    session = create_session("Test", None, "demo", "Hi", ["V1"], [])
    
    retrieved = get_session(session.id)
    assert retrieved is not None
    assert retrieved.name == "Test"
    
    # Non-existent session
    assert get_session("nonexistent") is None

def test_update_favorites(tmp_path, monkeypatch):
    monkeypatch.setattr("session_service.SESSIONS_DIR", tmp_path)
    
    session = create_session("Test", None, "demo", "Hi", ["V1", "V2"], [])
    assert session.favorites == []
    
    updated = update_favorites(session.id, ["V1"])
    assert updated.favorites == ["V1"]
    
    # Verify persistence
    retrieved = get_session(session.id)
    assert retrieved.favorites == ["V1"]
