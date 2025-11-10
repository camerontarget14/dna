# DNA Dailies Notes Assistant - Qt Desktop App

Professional PySide6/Qt desktop application for VFX dailies review with AI-powered note generation and real-time transcription.

## Features

### Core Functionality
- ✅ **Version Management** - Load and manage shot versions from ShotGrid or CSV
- ✅ **AI Note Generation** - Multi-LLM support (OpenAI, Claude, Gemini)
- ✅ **Real-time Transcription** - Vexa integration for meeting transcription
- ✅ **ShotGrid Integration** - Playlist loading, status updates, and web linking
- ✅ **Per-version Notes** - Persistent user notes and AI-generated summaries
- ✅ **Transcript Display** - Live transcript view with segment tracking
- ✅ **CSV Import/Export** - Batch version management without ShotGrid
- ✅ **Theme Customization** - Full dark theme with RPA color picker integration
- ✅ **Keyboard Shortcuts** - Efficient navigation and control

### UI Components
- **Meeting Widget** - Join/leave transcription meetings with status indicator
- **LLM Assistant** - Tabbed interface for configuring OpenAI, Claude, and Gemini
- **Playlists Widget** - ShotGrid playlist browser and CSV import/export
- **Version List** - Collapsible sidebar with version selection
- **Split View** - Resizable panels for AI notes, transcripts, and user notes
- **Status Management** - Version status dropdown (when ShotGrid enabled)

## Quick Start

### Prerequisites
- Python 3.12+
- Backend server running (see backend setup)

### Installation

1. **Create virtual environment**:
```bash
cd frontend_v3
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Start the backend server** (in a separate terminal):
```bash
cd ../backend
source venv/bin/activate
python -m uvicorn main:app --reload --port 8000
```
Backend will run on `http://localhost:8000`

4. **Run the Qt app**:
```bash
source venv/bin/activate
python main.py
```

## Configuration

### Frontend Configuration

The frontend can be configured via environment variables:

```bash
# Backend connection (default: http://localhost:8000)
export DNA_BACKEND_URL=http://localhost:8000

# Request timeout in seconds (default: 30)
export DNA_REQUEST_TIMEOUT=30

# Connection retry attempts (default: 3)
export DNA_RETRY_ATTEMPTS=3

# Enable debug logging (default: false)
export DNA_DEBUG=true

# Log level (default: INFO)
export DNA_LOG_LEVEL=DEBUG
```

**Frontend preferences** (theme, window size, etc.) are stored locally in:
- `~/.dna_dailies/frontend_preferences.json`

### Backend Configuration
Configure the backend by copying `.env.example` to `.env` in the `backend/` directory:

```bash
cd ../backend
cp .env.example .env
```

Edit `.env` with your credentials:

```bash
# Required: At least one LLM API key
OPENAI_API_KEY=sk-...
CLAUDE_API_KEY=sk-...
GEMINI_API_KEY=...

# Optional: ShotGrid integration
SHOTGRID_WEB_URL=https://yourstudio.shotgrid.autodesk.com
SHOTGRID_URL=https://yourstudio.shotgrid.autodesk.com
SHOTGRID_SCRIPT_NAME=your_script_name
SHOTGRID_API_KEY=your_api_key

# Optional: Vexa transcription
VEXA_API_KEY=your_vexa_key
VEXA_API_URL=https://api.vexa.com
```

### Frontend Configuration
The frontend app stores settings in `backend/.env` via the Preferences dialog (Ctrl+Shift+P).

Settings include:
- LLM API keys and prompts
- ShotGrid connection details
- Vexa transcription configuration
- UI preferences

## Project Structure

```
frontend_v3/
├── main.py                      # Application entry point
├── requirements.txt             # Python dependencies
├── README.md                    # This file
│
├── models/                      # Qt data models
│   └── version_list_model.py    # Version list model for UI binding
│
├── services/                    # External integrations
│   ├── backend_service.py       # Main backend API client (FastAPI)
│   ├── vexa_service.py          # Vexa transcription API client
│   └── color_picker_service.py  # Color picker integration
│
├── ui/                          # QML user interface
│   └── main.qml                 # Main application UI (2500+ lines)
│
└── widgets/                     # Custom Qt widgets
    ├── color_picker/            # RPA-style color picker widget
    │   ├── controller.py        # Color picker controller
    │   ├── model.py             # Color space models (RGB/TMI/HSV)
    │   └── view/                # Color picker UI components
    │       ├── view.py          # Main color picker view
    │       ├── color_monitor.py # Color display
    │       ├── palette.py       # Color palette
    │       ├── color_sliders/   # RGB/TMI/Saturation sliders
    │       └── eye_dropper/     # Screen color picker tool
    └── sub_widgets/
        └── color_circle.py      # Color wheel widget
```

## Keyboard Shortcuts

### General
- **Ctrl+Shift+P** - Open Preferences
- **Ctrl+Shift+T** - Open Theme Customizer

### UI Navigation
- **Ctrl+Shift+U** - Toggle top section (Meeting/LLM/Playlists)
- **Ctrl+Shift+S** - Toggle versions list sidebar
- **Ctrl+Shift+D** - Toggle between Notes and Transcript tabs

### Version Navigation
- **Ctrl+Shift+Up** - Previous version
- **Ctrl+Shift+Down** - Next version

### Notes & AI
- **Ctrl+Shift+A** - Add AI notes to user notes
- **Ctrl+Shift+R** - Regenerate AI notes

## Development

### Dependencies

**Core:**
- `PySide6>=6.8.0` - Qt GUI framework
- `requests>=2.31.0` - HTTP client for backend API

**Optional (for future use):**
- `websockets>=12.0` - WebSocket support
- `aiohttp>=3.9.0` - Async HTTP client

### Architecture

**Services Layer:**
- `backend_service.py` - Handles all backend communication, version management, LLM integration, ShotGrid API, Vexa transcription
- `vexa_service.py` - Vexa API client for real-time transcription
- `color_picker_service.py` - Wraps color picker widget for QML integration

**Models Layer:**
- `version_list_model.py` - Qt model for version list display with roles for QML binding

**UI Layer:**
- `main.qml` - QML-based interface with dark theme, keyboard shortcuts, and responsive layout

**Widgets Layer:**
- Custom color picker widget following ORI RPA design patterns

### Code Style
- **Qt Style**: Use Qt's signal/slot mechanism for component communication
- **QML Binding**: Properties exposed to QML via `@Property` decorators
- **Signals**: Qt signals for state changes (`pyqtSignal`)
- **Services**: Encapsulate external API calls in service classes

## Integrations

### ShotGrid
- Load playlists and versions
- Update version statuses
- Open versions in ShotGrid web UI
- Requires API credentials in backend `.env`

### Vexa Transcription
- Real-time meeting transcription
- Support for Google Meet, Microsoft Teams, Zoom
- Automatic transcript updates
- Requires Vexa API key in backend `.env`

### LLM Providers
- **OpenAI** - GPT models for note generation
- **Claude** - Anthropic Claude models
- **Gemini** - Google Gemini models
- Configurable prompts per provider
- Requires API keys in backend `.env`

## API Documentation

The backend provides comprehensive API documentation:

**Interactive API Docs:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

**Health Check:**
```bash
curl http://localhost:8000/health
```

Returns backend status and configured features:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-10T12:00:00",
  "python_version": "3.12.0",
  "features": {
    "shotgrid": true,
    "vexa_transcription": true,
    "llm_openai": true,
    "llm_claude": true,
    "llm_gemini": false
  }
}
```

**Full API Reference:**
- See `backend/API_DOCUMENTATION.md` for complete endpoint documentation
- See `backend/API_QUICK_REFERENCE.md` for quick lookup guide

## Troubleshooting

### Backend Connection Issues
- Ensure backend server is running on `http://localhost:8000`
- Test connection: `curl http://localhost:8000/health`
- Check backend logs for errors
- Verify `.env` file exists and is properly configured
- Check `DNA_BACKEND_URL` environment variable if using custom URL

### Version List Empty
- Check ShotGrid credentials in Preferences
- Try CSV import as alternative
- Verify backend can connect to ShotGrid API

### AI Notes Not Generating
- Verify at least one LLM API key is configured
- Check backend logs for API errors
- Ensure prompts are configured in Preferences

### Transcription Not Working
- Verify Vexa API key is configured
- Check meeting ID format
- Ensure backend can reach Vexa API

### Qt Style Warnings
- The app uses Qt Basic style for cross-platform consistency
- Style warnings are suppressed by design
- Native look can be restored by removing style override in `main.py`

## Known Issues

- Long file paths may cause issues on Windows (use shorter paths)
- Very large playlists (500+ versions) may cause performance issues
- Transcript updates are polled, not pushed (WebSocket support planned)

## Future Enhancements

- [ ] WebSocket support for real-time transcript push
- [ ] Package for distribution (PyInstaller/cx_Freeze)
- [ ] Plugin system for custom integrations
- [ ] Multi-user collaboration features
- [ ] Offline mode with local database
- [ ] Advanced search and filtering
- [ ] Export to PDF/Word reports

## Support

For issues, questions, or contributions, please contact the DNA team.

## License

Internal DNA project - All rights reserved.
