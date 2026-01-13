# Taiwan Voice Generator Implementation Plan

> **For Agent:** REQUIRED SUB-WORKFLOW: Use /superpowers:execute-plan to implement this plan task-by-task.

**Goal:** Build a web-based tool to generate and preview Taiwan Mandarin voices using Google Gemini TTS for client selection.

**Architecture:** FastAPI backend handles Gemini TTS API calls with parallel batch processing. Simple HTML/JS frontend displays voice cards, personas, and session history. Generated audio saved locally with metadata for reproducibility.

**Tech Stack:** Python 3.12+, FastAPI, google-genai SDK, HTML/CSS/JS, WAV audio

---

## Task 1: Project Setup

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/main.py`
- Create: `.env.example`
- Create: `README.md`

**Step 1: Create requirements.txt**

```txt
fastapi==0.115.0
uvicorn[standard]==0.32.0
google-genai==1.0.0
python-dotenv==1.0.1
aiofiles==24.1.0
pydantic==2.10.0
```

**Step 2: Create .env.example**

```
# Option 1: API Key
GEMINI_API_KEY=your-api-key-here

# Option 2: Service Account (leave API key blank)
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
GCP_PROJECT_ID=your-project-id
```

**Step 3: Create minimal main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Taiwan Voice Generator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok"}
```

**Step 4: Create backend/conftest.py**

```python
import sys
from pathlib import Path

# Add backend directory to python path for tests
sys.path.append(str(Path(__file__).parent))
```

**Step 5: Test server starts**

Run: `cd backend && pip install -r requirements.txt && uvicorn main:app --reload`
Expected: Server running at http://localhost:8000

**Step 6: Commit**

```bash
git init
git add .
git commit -m "chore: initial project setup"
```

---

## Task 2: Authentication Service

**Files:**
- Create: `backend/auth.py`
- Create: `backend/tests/test_auth.py`
- Modify: `backend/main.py`

**Step 1: Write auth tests**

`backend/tests/test_auth.py`:
```python
import pytest
import os
from unittest.mock import patch, MagicMock
from auth import get_genai_client, validate_credentials

def test_get_client_api_key():
    with patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key"}, clear=True):
        client = get_genai_client()
        assert client is not None
        # Client structure might differ, just checking it returns something reasonable

def test_validate_credentials_success():
    with patch("auth.get_genai_client") as mock_get:
        mock_get.return_value = MagicMock()
        with patch.dict(os.environ, {"GEMINI_API_KEY": "fake"}, clear=True):
            result = validate_credentials()
            assert result["valid"] is True
            assert result["method"] == "api_key"

def test_validate_credentials_failure():
    with patch.dict(os.environ, {}, clear=True):
        result = validate_credentials()
        assert result["valid"] is False
```

**Step 2: Create auth.py**

```python
import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

def get_genai_client() -> genai.Client:
    """Get Gemini client using API key or service account."""
    api_key = os.getenv("GEMINI_API_KEY")
    
    if api_key:
        return genai.Client(api_key=api_key)
    
    # Fall back to service account
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    project_id = os.getenv("GCP_PROJECT_ID")
    
    if credentials_path and project_id:
        return genai.Client(
            vertexai=True,
            project=project_id,
            location="us-central1"
        )
    
    raise ValueError("No valid credentials found. Set GEMINI_API_KEY or GOOGLE_APPLICATION_CREDENTIALS")

def validate_credentials() -> dict:
    """Validate credentials on startup."""
    try:
        client = get_genai_client()
        return {"valid": True, "method": "api_key" if os.getenv("GEMINI_API_KEY") else "service_account"}
    except Exception as e:
        return {"valid": False, "error": str(e)}
```

**Step 2: Add startup validation to main.py**

```python
from auth import validate_credentials

@app.on_event("startup")
async def startup():
    result = validate_credentials()
    if not result["valid"]:
        print(f"Warning: {result['error']}")
    else:
        print(f"Auth: {result['method']}")

@app.get("/auth/status")
async def auth_status():
    return validate_credentials()
```

**Step 4: Test auth endpoint**

Run: `cd backend && pytest tests/test_auth.py`
Expected: Tests passed

Run: `curl http://localhost:8000/auth/status`
Expected: `{"valid": true, "method": "api_key"}`

**Step 5: Commit**

```bash
git add backend/auth.py backend/tests/test_auth.py backend/main.py
git commit -m "feat: add authentication service"
```

---

## Task 3: Voice & Persona Data

**Files:**
- Create: `data/voices.json`
- Create: `data/personas.json`
- Create: `data/demo_texts.json`

**Step 1: Create voices.json**

```json
{
  "voices": [
    {"name": "Zephyr", "characteristic": "Bright"},
    {"name": "Puck", "characteristic": "Upbeat"},
    {"name": "Charon", "characteristic": "Informative"},
    {"name": "Kore", "characteristic": "Firm"},
    {"name": "Fenrir", "characteristic": "Excitable"},
    {"name": "Leda", "characteristic": "Youthful"},
    {"name": "Orus", "characteristic": "Firm"},
    {"name": "Aoede", "characteristic": "Breezy"},
    {"name": "Callirrhoe", "characteristic": "Easy-going"},
    {"name": "Autonoe", "characteristic": "Bright"},
    {"name": "Enceladus", "characteristic": "Breathy"},
    {"name": "Iapetus", "characteristic": "Clear"},
    {"name": "Umbriel", "characteristic": "Easy-going"},
    {"name": "Algieba", "characteristic": "Smooth"},
    {"name": "Despina", "characteristic": "Smooth"},
    {"name": "Erinome", "characteristic": "Clear"},
    {"name": "Algenib", "characteristic": "Gravelly"},
    {"name": "Rasalgethi", "characteristic": "Informative"},
    {"name": "Laomedeia", "characteristic": "Upbeat"},
    {"name": "Achernar", "characteristic": "Soft"},
    {"name": "Alnilam", "characteristic": "Firm"},
    {"name": "Schedar", "characteristic": "Even"},
    {"name": "Gacrux", "characteristic": "Mature"},
    {"name": "Pulcherrima", "characteristic": "Forward"},
    {"name": "Achird", "characteristic": "Friendly"},
    {"name": "Zubenelgenubi", "characteristic": "Casual"},
    {"name": "Vindemiatrix", "characteristic": "Gentle"},
    {"name": "Sadachbia", "characteristic": "Lively"},
    {"name": "Sadaltager", "characteristic": "Knowledgeable"},
    {"name": "Sulafat", "characteristic": "Warm"}
  ]
}
```

**Step 2: Create personas.json**

```json
{
  "personas": [
    {
      "id": "busy_boss",
      "name": "Busy Boss",
      "local_name": "Mang",
      "archetype": "SME Owner",
      "traits": "Impatient, abrupt, rushing",
      "tone_instructions": "Fast pace, annoyed tone. Interrupts often. Uses short sentences. Sounds distracted.",
      "recommended_voice": "Fenrir"
    },
    {
      "id": "polite_rejector",
      "name": "Polite Rejector",
      "local_name": "Pai-Se",
      "archetype": "Soft Rejector",
      "traits": "Very polite but firm non-buyer",
      "tone_instructions": "Soft, apologetic, slow pace. Gentle but refuses to engage. High pitch, breathy voice.",
      "recommended_voice": "Leda"
    },
    {
      "id": "skeptical_auntie",
      "name": "Skeptical Auntie",
      "local_name": "Fang Bei",
      "archetype": "Scammer-Aware",
      "traits": "Suspicious, thinks you are a fraud",
      "tone_instructions": "Suspicious, sharp tone. Questioning intonation. Lower pitch, guarded.",
      "recommended_voice": "Orus"
    },
    {
      "id": "apathetic_lead",
      "name": "Apathetic Lead",
      "local_name": "Sui Bian",
      "archetype": "Whatever Guy",
      "traits": "Low energy, non-committal",
      "tone_instructions": "Monotone, bored, low energy. Sounds tired. Long pauses between words.",
      "recommended_voice": "Umbriel"
    },
    {
      "id": "chatty_elder",
      "name": "Chatty Elder",
      "local_name": "Gong Wei",
      "archetype": "Lonely Senior",
      "traits": "Friendly but off-topic",
      "tone_instructions": "Warm, enthusiastic, slightly slower pace. Laughs while talking. Sounds like an older person.",
      "recommended_voice": "Sulafat"
    }
  ]
}
```

**Step 3: Create demo_texts.json**

```json
{
  "insurance_demo": "您好，我是專業保險顧問。今天想跟您介紹一款非常適合您的保障方案。這個方案不僅涵蓋意外傷害，還包括住院醫療給付。您現在方便聽我簡單說明一下嗎？",
  "test_phrases": [
    "您好，請問是王先生嗎？",
    "抱歉打擾您，請問現在方便說話嗎？",
    "好的，那我改天再跟您聯繫。",
    "謝謝您的時間，祝您有美好的一天。"
  ]
  ]
}
```

**Step 4: Write data loader tests**

`backend/tests/test_data.py`:
```python
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
```

**Step 5: Create data manager**

`backend/data_manager.py`:
```python
import json
from pathlib import Path

def load_voices(data_dir: Path = Path("../data")) -> list:
    with open(data_dir / "voices.json", encoding="utf-8") as f:
        return json.load(f)["voices"]

def load_personas(data_dir: Path = Path("../data")) -> dict:
    with open(data_dir / "personas.json", encoding="utf-8") as f:
        data = json.load(f)["personas"]
        return {p["id"]: p for p in data["personas"]}

def load_demo_texts(data_dir: Path = Path("../data")) -> dict:
    with open(data_dir / "demo_texts.json", encoding="utf-8") as f:
        return json.load(f)
```

**Step 6: Commit**

```bash
git add data/ backend/data_manager.py backend/tests/test_data.py
git commit -m "feat: add voice, persona, and demo text data"
```

---

## Task 4: TTS Service

**Files:**
- Create: `backend/tts_service.py`
- Create: `backend/models.py`
- Create: `backend/tests/test_tts.py`

**Step 1: Create models.py**

```python
from pydantic import BaseModel
from typing import Optional
from enum import Enum

class GeminiModel(str, Enum):
    FLASH = "gemini-2.5-flash"
    PRO = "gemini-2.5-pro"

class GenerateRequest(BaseModel):
    voice: str
    text: str
    persona_id: Optional[str] = None
    model: GeminiModel = GeminiModel.FLASH

class GenerateResponse(BaseModel):
    success: bool
    file_path: Optional[str] = None
    metadata_path: Optional[str] = None
    duration_seconds: Optional[float] = None
    error: Optional[str] = None
```

```

**Step 2: Write TTS tests**

`backend/tests/test_tts.py`:
```python
import pytest
from unittest.mock import MagicMock, patch
from tts_service import generate_speech
from models import GenerateRequest

@pytest.mark.asyncio
async def test_generate_speech_success(tmp_path):
    with patch("tts_service.get_genai_client") as mock_get_client:
        mock_response = MagicMock()
        mock_response.candidates[0].content.parts[0].inline_data.data = b"fake_audio"
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_get_client.return_value = mock_client
        
        with patch("tts_service.OUTPUT_DIR", tmp_path):
            with patch("tts_service.load_personas", return_value={}):
                req = GenerateRequest(voice="Test", text="Hello")
                res = await generate_speech(req)
                
                assert res.success is True
                assert (tmp_path / f"{res.file_path}").exists()
```

**Step 3: Create tts_service.py**

```python
import os
import json
import asyncio
from datetime import datetime
from pathlib import Path
from auth import get_genai_client
from models import GenerateRequest, GenerateResponse, GeminiModel

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

OUTPUT_DIR.mkdir(exist_ok=True)
from data_manager import load_personas

async def generate_speech(request: GenerateRequest) -> GenerateResponse:
    """Generate speech using Gemini TTS."""
    try:
        client = get_genai_client()
        personas = load_personas()
        
        # Build prompt with persona instructions
        prompt = request.text
        persona_name = "default"
        if request.persona_id and request.persona_id in personas:
            persona = personas[request.persona_id]
            persona_name = persona["name"] # Use readable name for file
            prompt = f"[Speaking style: {persona['tone_instructions']}]\n\n{request.text}"
        
        # Generate audio
        response = client.models.generate_content(
            model=request.model.value,
            contents=prompt,
            config={
                "response_modalities": ["AUDIO"],
                "speech_config": {
                    "voice_config": {"prebuilt_voice_config": {"voice_name": request.voice}}
                }
            }
        )
        
        # Save audio file
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        base_name = f"{timestamp}_{request.voice}_{persona_name}"
        audio_path = OUTPUT_DIR / f"{base_name}.wav"
        metadata_path = OUTPUT_DIR / f"{base_name}.txt"
        
        # Extract and save audio
        audio_data = response.candidates[0].content.parts[0].inline_data.data
        with open(audio_path, "wb") as f:
            f.write(audio_data)
        
        # Save metadata
        metadata = {
            "voice": request.voice,
            "persona": persona_name,
            "model": request.model.value,
            "text": request.text,
            "generated_at": timestamp,
        }
        if request.persona_id and request.persona_id in personas:
            metadata["tone_instructions"] = personas[request.persona_id]["tone_instructions"]
        
        with open(metadata_path, "w", encoding="utf-8") as f:
            for k, v in metadata.items():
                f.write(f"{k}: {v}\n")
        
        return GenerateResponse(
            success=True,
            file_path=str(audio_path),
            metadata_path=str(metadata_path)
        )
        
    except Exception as e:
        return GenerateResponse(success=False, error=str(e))
```

**Step 3: Add endpoint to main.py**

```python
from tts_service import generate_speech
from models import GenerateRequest, GenerateResponse

@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    return await generate_speech(request)
```

**Step 5: Test generation**

Run: `cd backend && pytest tests/test_tts.py`
Expected: Tests passed

Run: `curl -X POST http://localhost:8000/generate -H "Content-Type: application/json" -d '{"voice":"Zephyr","text":"您好"}'`
Expected: JSON with file_path to generated WAV

**Step 6: Commit**

```bash
git add backend/
git commit -m "feat: add TTS generation service"
```

---

## Task 5: Batch Generation

**Files:**
- Modify: `backend/tts_service.py`
- Modify: `backend/main.py`
- Modify: `backend/tests/test_tts.py`

**Step 1: Add batch tests**

Append to `backend/tests/test_tts.py`:
```python
@pytest.mark.asyncio
async def test_batch_generate():
    with patch("tts_service.generate_speech") as mock_single:
        mock_single.return_value = MagicMock(success=True)
        from tts_service import generate_batch
        
        voices = ["V1", "V2", "V3"]
        results = await generate_batch(voices, "text", None, "gemini-2.5-flash")
        assert len(results) == 3
        assert mock_single.call_count == 3
```

**Step 2: Add batch function to tts_service.py**

```python
from typing import List

async def generate_batch(
    voices: List[str],
    text: str,
    persona_id: str | None,
    model: GeminiModel,
    concurrency: int = 5
) -> List[GenerateResponse]:
    """Generate speech for multiple voices in parallel."""
    semaphore = asyncio.Semaphore(concurrency)
    
    async def generate_with_limit(voice: str):
        async with semaphore:
            request = GenerateRequest(
                voice=voice,
                text=text,
                persona_id=persona_id,
                model=model
            )
            return await generate_speech(request)
    
    tasks = [generate_with_limit(v) for v in voices]
    return await asyncio.gather(*tasks)
```

**Step 3: Add batch endpoint to main.py**

```python
from tts_service import generate_batch
from models import GeminiModel

class BatchRequest(BaseModel):
    voices: List[str]
    text: str
    persona_id: Optional[str] = None
    model: GeminiModel = GeminiModel.FLASH

@app.post("/batch")
async def batch_generate(request: BatchRequest):
    results = await generate_batch(
        request.voices,
        request.text,
        request.persona_id,
        request.model
    )
    return {"results": results, "total": len(results)}
```

**Step 4: Test batch**

Run: `pytest backend/tests/test_tts.py`

Run: `curl -X POST http://localhost:8000/batch -H "Content-Type: application/json" -d '{"voices":["Zephyr","Puck"],"text":"您好"}'`

**Step 5: Commit**

```bash
git add backend/
git commit -m "feat: add parallel batch generation"
```

---

## Task 6: Session Management

**Files:**
- Create: `backend/session_service.py`
- Create: `backend/tests/test_session.py`
- Modify: `backend/main.py`

**Step 1: Write session tests**

`backend/tests/test_session.py`:
```python
from session_service import create_session, list_sessions, SESSIONS_DIR
import pytest

def test_create_list_sessions(tmp_path):
    with pytest.MonkeyPatch.context() as m:
        m.setattr("session_service.SESSIONS_DIR", tmp_path)
        create_session("Test", None, "type", "content", [], [])
        
        sessions = list_sessions()
        assert len(sessions) == 1
        assert sessions[0].name == "Test"
```

**Step 2: Create session_service.py**

```python
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
```

**Step 3: Add session endpoints to main.py**

```python
from session_service import list_sessions, get_session, update_favorites

@app.get("/sessions")
async def get_sessions():
    return list_sessions()

@app.get("/sessions/{session_id}")
async def get_session_by_id(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@app.patch("/sessions/{session_id}/favorites")
async def update_session_favorites(session_id: str, favorites: List[str]):
    session = update_favorites(session_id, favorites)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session
```

**Step 4: Commit**

```bash
git add backend/
git commit -m "feat: add session management"
```

---

## Task 7: Frontend - Main Layout

**Files:**
- Create: `frontend/index.html`
- Create: `frontend/styles.css`

**Step 1: Create index.html**

```html
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Taiwan Voice Generator</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div class="app">
        <aside class="sidebar">
            <h2>📜 History</h2>
            <button id="new-session" class="btn-new">+ New Session</button>
            <div id="session-list" class="session-list"></div>
        </aside>
        
        <main class="main-content">
            <header class="header">
                <h1>🎙️ Taiwan Voice Generator</h1>
                <div id="api-status" class="api-status">Checking...</div>
            </header>
            
            <section class="settings">
                <label>Model:</label>
                <select id="model-select">
                    <option value="gemini-2.5-flash">Flash (Fast)</option>
                    <option value="gemini-2.5-pro">Pro (Quality)</option>
                </select>
            </section>
            
            <section class="voices">
                <h2>Voice Selection</h2>
                <div class="filter-bar">
                    <button class="filter-btn active" data-filter="all">All</button>
                </div>
                <div id="voice-grid" class="voice-grid"></div>
            </section>
            
            <section class="personas">
                <h2>Persona</h2>
                <div id="persona-grid" class="persona-grid"></div>
                <div id="persona-info" class="persona-info"></div>
            </section>
            
            <section class="text-input">
                <h2>Text Input</h2>
                <div class="tabs">
                    <button class="tab active" data-tab="demo">Insurance Demo</button>
                    <button class="tab" data-tab="phrases">Test Phrases</button>
                    <button class="tab" data-tab="custom">Custom</button>
                </div>
                <textarea id="text-content" rows="4"></textarea>
            </section>
            
            <section class="actions">
                <button id="generate-btn" class="btn-primary">▶ Generate Selected</button>
                <button id="batch-btn" class="btn-secondary">🔄 Batch All 30 Voices</button>
                <div id="progress" class="progress" style="display:none">
                    <div id="progress-bar" class="progress-bar"></div>
                    <span id="progress-text">0/30</span>
                </div>
            </section>
            
            <section class="results">
                <h2>Generated Audio</h2>
                <table id="results-table">
                    <thead>
                        <tr>
                            <th>Voice</th>
                            <th>Persona</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody></tbody>
                </table>
            </section>
            
            <section class="export">
                <h2>Export for Gemini Live</h2>
                <pre id="export-config">{}</pre>
                <button id="copy-config" class="btn-secondary">📋 Copy Config</button>
            </section>
        </main>
    </div>
    <script src="app.js"></script>
</body>
</html>
```

**Step 2: Create styles.css** (abbreviated for space)

```css
* { box-sizing: border-box; margin: 0; padding: 0; }

:root {
    --bg-dark: #0f0f1a;
    --bg-card: #1a1a2e;
    --accent: #6c63ff;
    --accent-glow: rgba(108, 99, 255, 0.3);
    --text: #e0e0e0;
    --text-dim: #888;
}

body {
    font-family: 'Segoe UI', sans-serif;
    background: var(--bg-dark);
    color: var(--text);
}

.app {
    display: flex;
    min-height: 100vh;
}

.sidebar {
    width: 260px;
    background: var(--bg-card);
    padding: 1rem;
    border-right: 1px solid #333;
}

.main-content {
    flex: 1;
    padding: 2rem;
    overflow-y: auto;
}

.voice-grid, .persona-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    gap: 0.75rem;
    margin-top: 1rem;
}

.voice-card, .persona-card {
    background: var(--bg-card);
    border: 2px solid transparent;
    border-radius: 8px;
    padding: 1rem;
    cursor: pointer;
    transition: all 0.2s;
}

.voice-card:hover, .persona-card:hover {
    border-color: var(--accent);
    box-shadow: 0 0 12px var(--accent-glow);
}

.voice-card.selected, .persona-card.selected {
    border-color: var(--accent);
    background: rgba(108, 99, 255, 0.1);
}

.btn-primary {
    background: var(--accent);
    color: white;
    border: none;
    padding: 0.75rem 1.5rem;
    border-radius: 6px;
    cursor: pointer;
    font-size: 1rem;
}

.btn-primary:hover {
    background: #5a52e0;
}

.progress {
    margin-top: 1rem;
}

.progress-bar {
    height: 8px;
    background: var(--accent);
    border-radius: 4px;
    transition: width 0.3s;
}
```

**Step 3: Commit**

```bash
git add frontend/
git commit -m "feat: add frontend layout and styles"
```

---

## Task 8: Frontend - JavaScript Logic

**Files:**
- Create: `frontend/app.js`

**Step 1: Create app.js**

```javascript
const API = 'http://localhost:8000';
let voices = [];
let personas = [];
let selectedVoice = null;
let selectedPersona = null;
let demoTexts = {};

async function init() {
    await checkApiStatus();
    await loadData();
    renderVoices();
    renderPersonas();
    loadSessions();
    setupEventListeners();
}

async function checkApiStatus() {
    try {
        const res = await fetch(`${API}/auth/status`);
        const data = await res.json();
        document.getElementById('api-status').textContent = 
            data.valid ? '✓ Connected' : '✗ Not connected';
        document.getElementById('api-status').className = 
            'api-status ' + (data.valid ? 'connected' : 'error');
    } catch {
        document.getElementById('api-status').textContent = '✗ API Offline';
    }
}

async function loadData() {
    const [v, p, t] = await Promise.all([
        fetch('data/voices.json').then(r => r.json()),
        fetch('data/personas.json').then(r => r.json()),
        fetch('data/demo_texts.json').then(r => r.json())
    ]);
    voices = v.voices;
    personas = p.personas;
    demoTexts = t;
    document.getElementById('text-content').value = demoTexts.insurance_demo;
}

function renderVoices() {
    const grid = document.getElementById('voice-grid');
    grid.innerHTML = voices.map(v => `
        <div class="voice-card" data-voice="${v.name}">
            <div class="voice-name">${v.name}</div>
            <div class="voice-char">${v.characteristic}</div>
        </div>
    `).join('');
}

function renderPersonas() {
    const grid = document.getElementById('persona-grid');
    grid.innerHTML = personas.map(p => `
        <div class="persona-card" data-persona="${p.id}">
            <div class="persona-name">${p.name}</div>
            <div class="persona-local">${p.local_name}</div>
            <div class="persona-rec">Rec: ${p.recommended_voice}</div>
        </div>
    `).join('');
}

async function loadSessions() {
    try {
        const res = await fetch(`${API}/sessions`);
        const sessions = await res.json();
        const list = document.getElementById('session-list');
        list.innerHTML = sessions.map(s => `
            <div class="session-item" data-id="${s.id}">
                <div class="session-name">${s.name}</div>
                <div class="session-meta">${s.voices_tested.length} voices</div>
            </div>
        `).join('');
    } catch (e) {
        console.log('No sessions yet');
    }
}

function setupEventListeners() {
    // Voice selection
    document.getElementById('voice-grid').addEventListener('click', e => {
        const card = e.target.closest('.voice-card');
        if (card) {
            document.querySelectorAll('.voice-card').forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
            selectedVoice = card.dataset.voice;
            updateExportConfig();
        }
    });

    // Persona selection
    document.getElementById('persona-grid').addEventListener('click', e => {
        const card = e.target.closest('.persona-card');
        if (card) {
            document.querySelectorAll('.persona-card').forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
            selectedPersona = card.dataset.persona;
            const persona = personas.find(p => p.id === selectedPersona);
            document.getElementById('persona-info').textContent = 
                `Tone: ${persona.tone_instructions}`;
            updateExportConfig();
        }
    });

    // Generate button
    document.getElementById('generate-btn').addEventListener('click', generateSelected);
    document.getElementById('batch-btn').addEventListener('click', generateBatch);
    document.getElementById('copy-config').addEventListener('click', copyConfig);

    // Tabs
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            const type = tab.dataset.tab;
            if (type === 'demo') {
                document.getElementById('text-content').value = demoTexts.insurance_demo;
            } else if (type === 'phrases') {
                document.getElementById('text-content').value = demoTexts.test_phrases.join('\n');
            } else {
                document.getElementById('text-content').value = '';
            }
        });
    });
}

async function generateSelected() {
    if (!selectedVoice) {
        alert('Please select a voice');
        return;
    }
    const text = document.getElementById('text-content').value;
    const model = document.getElementById('model-select').value;
    
    const res = await fetch(`${API}/generate`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            voice: selectedVoice,
            text: text,
            persona_id: selectedPersona,
            model: model
        })
    });
    const data = await res.json();
    if (data.success) {
        addResultRow(selectedVoice, selectedPersona, data.file_path);
    } else {
        alert('Error: ' + data.error);
    }
}

async function generateBatch() {
    const text = document.getElementById('text-content').value;
    const model = document.getElementById('model-select').value;
    const voiceNames = voices.map(v => v.name);
    
    document.getElementById('progress').style.display = 'block';
    
    const res = await fetch(`${API}/batch`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            voices: voiceNames,
            text: text,
            persona_id: selectedPersona,
            model: model
        })
    });
    const data = await res.json();
    
    document.getElementById('progress').style.display = 'none';
    data.results.forEach((r, i) => {
        if (r.success) {
            addResultRow(voiceNames[i], selectedPersona, r.file_path);
        }
    });
}

function addResultRow(voice, persona, filePath) {
    const tbody = document.querySelector('#results-table tbody');
    const row = document.createElement('tr');
    row.innerHTML = `
        <td>${voice}</td>
        <td>${persona || 'default'}</td>
        <td>
            <button onclick="playAudio('${filePath}')">▶</button>
            <button onclick="toggleFavorite(this)">⭐</button>
            <button onclick="downloadFile('${filePath}')">💾</button>
        </td>
    `;
    tbody.appendChild(row);
}

function playAudio(path) {
    const audio = new Audio(`${API}/files/${encodeURIComponent(path)}`);
    audio.play();
}

function updateExportConfig() {
    const config = {
        voice: selectedVoice,
        persona: selectedPersona,
        model: document.getElementById('model-select').value
    };
    document.getElementById('export-config').textContent = JSON.stringify(config, null, 2);
}

function copyConfig() {
    const config = document.getElementById('export-config').textContent;
    navigator.clipboard.writeText(config);
    alert('Config copied!');
}

init();
```

**Step 2: Add static file serving to main.py**

```python
from fastapi.responses import FileResponse

@app.get("/files/{file_path:path}")
async def serve_file(file_path: str):
    return FileResponse(file_path)

# Serve frontend
app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")
```

**Step 3: Test full application**

Run: `cd backend && uvicorn main:app --reload`
Open: http://localhost:8000

**Step 4: Commit**

```bash
git add .
git commit -m "feat: complete frontend implementation"
```

---

## Task 9: Documentation

**Files:**
- Create: `README.md`
- Create: `docs/gemini-live-vs-separated-stt-tts.md`

**Step 1: Create README.md**

```markdown
# Taiwan Voice Generator

Generate and preview Taiwan Mandarin voices using Google Gemini TTS for client selection.

## Features

- 30 Gemini voice options with characteristics
- 5 Taiwan-specific personas (Busy Boss, Polite Rejector, etc.)
- Batch generation with parallel processing
- Session history for tracking experiments
- Export voice config for Gemini Live integration

## Setup

1. Install dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. Configure credentials (choose one):
   ```bash
   # Option 1: API Key
   cp .env.example .env
   # Edit .env with your GEMINI_API_KEY
   
   # Option 2: Service Account
   # Set GOOGLE_APPLICATION_CREDENTIALS and GCP_PROJECT_ID
   ```

3. Run:
   ```bash
   uvicorn main:app --reload
   ```

4. Open http://localhost:8000

## Usage

1. Select a voice from the grid
2. Choose a persona (or use default)
3. Enter text or use demo script
4. Click Generate or Batch All
5. Listen to results and mark favorites
6. Export config for Gemini Live
```

**Step 2: Commit**

```bash
git add .
git commit -m "docs: add README and architecture docs"
```

---

## Verification Checklist

| Test | Command/Action | Expected |
|------|----------------|----------|
| Server starts | `uvicorn main:app` | No errors |
| Auth works | `GET /auth/status` | `{"valid": true}` |
| Single generate | `POST /generate` | WAV file created |
| Batch generate | `POST /batch` | Multiple WAV files |
| Sessions persist | Refresh browser | Sessions reload |
| Audio plays | Click play button | Audio plays |
| Export config | Click copy | Valid JSON |

---

**Plan complete and saved to `docs/plans/2026-01-14-taiwan-voice-generator.md`.**

Ready to execute with `/superpowers:execute-plan`?
