from data_manager import load_voices, load_personas
import json

def test_load_voices(tmp_path):
    d = tmp_path / "data"
    d.mkdir()
    (d / "voices.json").write_text(json.dumps({"voices": [{"name": "Test"}]}), encoding="utf-8")
    
    voices = load_voices(data_dir=d)
    assert len(voices) == 1
    assert voices[0]["name"] == "Test"

def test_load_personas(tmp_path):
    d = tmp_path / "data"
    d.mkdir()
    (d / "personas.json").write_text(json.dumps({"personas": [{"id": "p1"}]}), encoding="utf-8")
    
    personas = load_personas(data_dir=d)
    assert "p1" in personas
