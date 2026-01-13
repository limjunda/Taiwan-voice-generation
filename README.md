# Taiwan Voice Generator

🎙️ Generate and preview Taiwan Mandarin voices using Google Gemini TTS for client selection.

## Features

- **30 Gemini voice options** with characteristics (Bright, Firm, Warm, etc.)
- **5 Taiwan-specific personas** (Busy Boss, Polite Rejector, Skeptical Auntie, etc.)
- **Batch generation** with parallel processing (5 concurrent)
- **Session history** for tracking experiments
- **Export voice config** for Gemini Live integration

## Quick Start

### 1. Install dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure credentials

Copy the example file and add your API key:
```bash
cp .env.example .env
```

Edit `.env`:
```ini
# Option 1: API Key (recommended for local dev)
GEMINI_API_KEY=your-api-key-here

# Option 2: Service Account
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
GCP_PROJECT_ID=your-project-id
```

### 3. Run the server
```bash
cd backend
python -m uvicorn main:app --reload
```

### 4. Open the UI
Navigate to: http://localhost:8000

## Usage

1. **Select a voice** from the grid (use filters to narrow down)
2. **Choose a persona** to apply Taiwan-specific speaking styles
3. **Enter text** or use the insurance demo script
4. **Click Generate** for single voice, or **Batch All** for all 30 voices
5. **Listen and compare** the generated audio
6. **Mark favorites** and export the config for Gemini Live

## Project Structure

```
Taiwan-voice generation/
├── backend/
│   ├── main.py           # FastAPI application
│   ├── auth.py           # API key / Service Account auth
│   ├── tts_service.py    # Gemini TTS generation
│   ├── session_service.py # Session history
│   ├── models.py         # Pydantic models
│   └── tests/            # Pytest tests
├── frontend/
│   ├── index.html        # Main UI
│   ├── styles.css        # Dark theme styles
│   ├── app.js            # UI logic
│   └── data/             # Voice/persona JSON
├── data/
│   ├── voices.json       # 30 voice definitions
│   ├── personas.json     # 5 Taiwan personas
│   └── demo_texts.json   # Sample texts
├── output/               # Generated audio (git-ignored)
└── sessions/             # Session history (git-ignored)
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/auth/status` | Check credentials |
| POST | `/generate` | Generate single voice |
| POST | `/batch` | Generate multiple voices |
| GET | `/sessions` | List all sessions |
| GET | `/sessions/{id}` | Get session details |
| PATCH | `/sessions/{id}/favorites` | Update favorites |

## Personas

| Name | Local Name | Traits |
|------|------------|--------|
| Busy Boss | Mang | Impatient, abrupt, rushing |
| Polite Rejector | Pai-Se | Very polite but firm non-buyer |
| Skeptical Auntie | Fang Bei | Suspicious, scammer-aware |
| Apathetic Lead | Sui Bian | Low energy, non-committal |
| Chatty Elder | Gong Wei | Friendly but off-topic |

## License

Internal use for AI Training Suite project.
