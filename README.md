# Taiwan Voice Generator

🎙️ Generate and preview Taiwan Mandarin voices using Google Gemini TTS for client selection.

## Features

- **30 Gemini voice options** with gender (♂/♀) and characteristic filters
- **5+ Taiwan-specific personas** (Busy Boss, Polite Rejector, Skeptical Auntie, etc.)
- **Custom personas** - create and save your own personas locally
- **Session-based organization** - each session gets its own folder
- **Batch generation** with parallel processing (5 concurrent)
- **Audio player** with playback controls and metadata display
- **Export voice config** for Gemini Live integration

## Quick Start

### 1. Clone and setup virtual environment

```bash
# Clone the repository
git clone https://github.com/your-username/Taiwan-voice-generation.git
cd Taiwan-voice-generation

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 2. Install dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3. Configure credentials

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

### 4. Run the server

```bash
cd backend
python -m uvicorn main:app --reload
```

### 5. Open the UI

Navigate to: http://localhost:8000

## Usage

1. **Select a voice** from the grid (filter by gender ♂/♀ or characteristic)
2. **Choose a persona** to apply Taiwan-specific speaking styles
3. **Enter text** or use the insurance demo script
4. **Click Generate** for single voice, or **Batch All** for all 30 voices
5. **Listen and compare** using the built-in audio player
6. **Mark favorites** and export the config for Gemini Live

### Custom Personas

1. Click **"+ Custom"** in the Persona section
2. Fill in the form with name, tone instructions, etc.
3. Double-click a custom persona to edit it
4. Custom personas are saved locally in `data/custom_personas.json`

### Session Management

- Click **"+ New Session"** to create a session folder
- All generated audio goes into the active session's folder
- Click on sessions in the sidebar to switch between them

## Project Structure

```
Taiwan-voice generation/
├── backend/
│   ├── main.py           # FastAPI application
│   ├── auth.py           # API key / Service Account auth
│   ├── tts_service.py    # Gemini TTS generation
│   ├── session_service.py # Session management
│   ├── data_manager.py   # Persona/voice data
│   ├── models.py         # Pydantic models
│   └── tests/            # Pytest tests
├── frontend/
│   ├── index.html        # Main UI
│   ├── styles.css        # Dark theme styles
│   ├── app.js            # UI logic
│   └── data/             # Voice/persona JSON
├── data/
│   ├── voices.json       # 30 voice definitions with gender
│   ├── personas.json     # 5 Taiwan personas
│   ├── custom_personas.json  # User-created personas
│   └── demo_texts.json   # Sample texts
├── output/               # Legacy audio files (git-ignored)
└── venv/                 # Virtual environment (git-ignored)
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/auth/status` | Check credentials |
| POST | `/generate` | Generate single voice |
| POST | `/batch` | Generate multiple voices |
| GET | `/audio` | List audio files |
| GET | `/audio?legacy=true` | List legacy audio files |
| GET | `/sessions` | List all sessions |
| POST | `/sessions` | Create new session |
| POST | `/sessions/active/{id}` | Set active session |
| GET | `/custom-personas` | List custom personas |
| POST | `/custom-personas` | Create custom persona |
| PUT | `/custom-personas/{id}` | Update custom persona |
| DELETE | `/custom-personas/{id}` | Delete custom persona |

## Personas

| Name | Local Name | Traits |
|------|------------|--------|
| Busy Boss | Mang | Impatient, abrupt, rushing |
| Polite Rejector | Pai-Se | Very polite but firm non-buyer |
| Skeptical Auntie | Fang Bei | Suspicious, scammer-aware |
| Apathetic Lead | Sui Bian | Low energy, non-committal |
| Chatty Elder | Gong Wei | Friendly but off-topic |

## Running Tests

```bash
cd backend
python -m pytest tests/ -v
```

## License

Internal use for AI Training Suite project.
