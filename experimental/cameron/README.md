# DNA Dailies Notes Assistant - Cameron Edition

Multi-platform dailies review tool with real-time transcription, collaborative notes, and AI assistance.

## Project Structure

```
cameron/
├── backend/              # Shared backend server (Python FastAPI)
│   ├── main.py          # Main server entry point
│   ├── venv/            # Python virtual environment
│   └── ...
│
├── frontend_v1/         # React web application
│   ├── src/             # React/TypeScript source
│   ├── package.json     # Node dependencies
│   └── ...
│
├── frontend_v2/         # Qt desktop application (in development)
│   ├── venv/            # Python virtual environment
│   └── ...
│
├── shared/              # Shared code between frontends
│   └── dna-frontend-framework/
│
└── docs/                # Documentation
    ├── README.md        # Main documentation
    ├── ARCHITECTURE.md  # System architecture
    ├── QUICKSTART.md    # Quick start guide
    └── ...
```

## Getting Started

### Backend (Required for both frontends)

```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

Backend runs on `http://localhost:8000`

### Frontend v1 (React Web App)

```bash
cd frontend_v1
npm install
npm run dev
```

Access at `http://localhost:5173`

### Frontend v2 (Qt Desktop App)

```bash
cd frontend_v2
source venv/bin/activate
python main.py
```

## Features

- **Real-time Transcription** via Vexa integration
- **Collaborative Notes** with user attribution
- **AI-Assisted Note Generation** (OpenAI, Claude, Llama)
- **Playlist Management** (ShotGrid, CSV)
- **Version Management** with per-version transcripts
- **CSV Export** for review sessions

## Documentation

See the `docs/` directory for detailed documentation:
- **README.md** - Full feature documentation
- **ARCHITECTURE.md** - Technical architecture
- **QUICKSTART.md** - Getting started guide
- **SHOTGRID_INTEGRATION.md** - ShotGrid setup

## Development

Both frontends connect to the same backend server. Run the backend first, then launch either frontend for development.

**Frontend v1** is the production-ready web interface.
**Frontend v2** is the Qt desktop version (in development) for native integration and RV compatibility.
