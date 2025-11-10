# DNA Dailies Notes Assistant - Architecture

## Overview

The DNA Dailies Notes Assistant is built with a **decoupled client-server architecture**, allowing the backend to serve multiple frontend clients.

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   PySide6    │  │   Web App    │  │     CLI      │         │
│  │   Qt Client  │  │   (Future)   │  │   (Future)   │         │
│  │  (frontend_v3)│  │              │  │              │         │
│  └───────┬──────┘  └──────┬───────┘  └──────┬───────┘         │
│          │                │                  │                  │
│          └────────────────┼──────────────────┘                  │
│                           │ HTTP/REST                           │
└───────────────────────────┼─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND API LAYER                           │
│                    (FastAPI - backend/)                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Core API Endpoints                           │  │
│  │  • /health - Health check and feature status            │  │
│  │  • /settings - Configuration management                  │  │
│  │  • /versions - Version CRUD operations                   │  │
│  │  • /notes - AI note generation                           │  │
│  │  • /playlists - CSV import                               │  │
│  │  • /shotgrid - ShotGrid integration                      │  │
│  │  • /email - Email service                                │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└───────────────┬──────────────────┬──────────────────────────────┘
                │                  │
                ▼                  ▼
┌────────────────────────┐  ┌────────────────────────┐
│  EXTERNAL SERVICES     │  │  DATA STORAGE          │
│                        │  │                        │
│  • OpenAI API          │  │  • In-memory versions  │
│  • Claude API          │  │  • .env config file    │
│  • Gemini API          │  │  • CSV import/export   │
│  • Vexa Transcription  │  │                        │
│  • ShotGrid API        │  │                        │
│  • Gmail API           │  │                        │
└────────────────────────┘  └────────────────────────┘
```

## Key Architectural Principles

### 1. **Backend Independence**
The backend is a standalone FastAPI service that:
- Has no knowledge of frontend implementation
- Communicates only via HTTP/REST
- Stores configuration in its own `.env` file
- Can be deployed separately from any frontend

### 2. **Frontend Flexibility**
Frontends connect to backend via HTTP:
- Backend URL is configurable via environment variable
- Multiple frontends can connect to same backend
- Frontends can be in any language/framework
- Each frontend can have local preferences

### 3. **Stateless API**
The backend API is mostly stateless:
- Versions stored in-memory (temporary)
- Configuration persisted in `.env` file
- No user authentication (single-user application)
- Suitable for local desktop deployment

## Backend Services

### Core Services (`backend/`)

| Service | File | Purpose |
|---------|------|---------|
| Main API | `main.py` | FastAPI app, CORS, health checks |
| Version Service | `version_service.py` | Version CRUD, notes, transcript |
| Note Service | `note_service.py` | LLM integration (OpenAI/Claude/Gemini) |
| Playlist Service | `playlist.py` | CSV import |
| ShotGrid Service | `shotgrid_service.py` | ShotGrid API integration |
| Settings Service | `settings_service.py` | Configuration persistence |
| Email Service | `email_service.py` | Gmail integration |

### API Endpoints

**28 total endpoints** organized by service:

```
/                           GET   - API info
/health                     GET   - Health check
/docs                       GET   - Interactive API docs
/settings                   GET   - Get settings
/settings                   POST  - Update settings
/settings/save-partial      POST  - Partial settings update
/versions                   GET   - List versions
/versions                   POST  - Create version
/versions/{id}              GET   - Get version details
/versions/{id}              DELETE- Delete version
/versions/{id}/notes        GET   - Get version notes
/versions/{id}/notes        PUT   - Update version notes
/versions/export/csv        GET   - Export to CSV
/versions/import/csv        POST  - Import from CSV
/notes/generate             POST  - Generate AI notes
/playlists/import-csv       POST  - Import CSV playlist
/shotgrid/*                 *     - 9 ShotGrid endpoints
/email/send                 POST  - Send email
```

Full API documentation: [`backend/API_DOCUMENTATION.md`](backend/API_DOCUMENTATION.md)

## Frontend Architecture

### Current Frontend: PySide6 Qt (`frontend_v3/`)

**Technology Stack:**
- PySide6 6.8+ (Qt for Python)
- QML for UI
- Python 3.12+

**Architecture Layers:**

```
frontend_v3/
├── main.py                  # Entry point, Qt application
├── config.py                # Configuration management
│
├── services/                # Backend communication
│   ├── backend_service.py   # HTTP client for backend API
│   ├── vexa_service.py      # Vexa API wrapper
│   └── color_picker_service.py
│
├── models/                  # Qt data models
│   └── version_list_model.py
│
├── ui/                      # QML interface
│   └── main.qml             # Main UI definition
│
└── widgets/                 # Custom widgets
    └── color_picker/        # RPA color picker
```

**Communication Pattern:**
```
QML UI
  ↕ Qt Signals/Slots
Python Backend Service
  ↕ HTTP REST
FastAPI Backend
```

### Configuration System

**Frontend Config (`config.py`):**
- Backend URL (env: `DNA_BACKEND_URL`)
- Request timeout (env: `DNA_REQUEST_TIMEOUT`)
- Retry attempts (env: `DNA_RETRY_ATTEMPTS`)
- Debug mode (env: `DNA_DEBUG`)
- Local preferences in `~/.dna_dailies/`

**Backend Config (`.env`):**
- LLM API keys and prompts
- ShotGrid credentials
- Vexa API key
- Email configuration

## Data Flow Examples

### Example 1: Creating a Version

```
1. User clicks "Import CSV" in Qt frontend
2. Frontend calls backend_service.import_csv()
3. backend_service makes HTTP POST to /playlists/import-csv
4. Backend parses CSV, creates versions in memory
5. Backend returns version list as JSON
6. Frontend updates version_list_model
7. QML UI refreshes version list display
```

### Example 2: Generating AI Notes

```
1. User clicks "Regenerate AI Notes" for a version
2. Frontend calls backend_service.regenerate_ai_notes(version_id)
3. backend_service makes HTTP POST to /notes/generate
4. Backend:
   a. Retrieves version transcript from memory
   b. Calls OpenAI/Claude/Gemini API
   c. Stores generated notes with version
   d. Returns notes as JSON
5. Frontend updates UI with new AI notes
6. User can add notes to their manual notes
```

### Example 3: ShotGrid Integration

```
1. User configures ShotGrid in Preferences
2. Frontend saves to backend via POST /settings/save-partial
3. Backend persists to .env file
4. User clicks "Load ShotGrid Playlist"
5. Frontend calls GET /shotgrid/projects
6. Backend authenticates with ShotGrid API
7. Returns project list
8. User selects project, loads playlist
9. Backend fetches versions from ShotGrid
10. Versions displayed in frontend
```

## Deployment Scenarios

### Scenario 1: Single User Desktop (Current)
```
[Laptop]
  ├── Backend (localhost:8000)
  └── Qt Frontend → connects to localhost
```

### Scenario 2: Shared Backend
```
[Server: backend.studio.com:8000]
  └── Backend API

[Artist Workstation 1]
  └── Qt Frontend → connects to backend.studio.com

[Artist Workstation 2]
  └── Qt Frontend → connects to backend.studio.com

[Artist Workstation 3]
  └── Web Frontend → connects to backend.studio.com
```

### Scenario 3: Multiple Backends
```
[Dev Server]
  └── Backend (dev.studio.com:8000)

[Staging Server]
  └── Backend (staging.studio.com:8000)

[Production Server]
  └── Backend (prod.studio.com:8000)

[Artist]
  └── Frontend (DNA_BACKEND_URL=prod.studio.com:8000)
```

## Security Considerations

**Current State (Local Desktop):**
- No authentication required
- CORS allows all origins
- Designed for single-user local deployment
- Credentials stored in backend `.env` file

**For Multi-User Deployment:**
Would need to add:
- API key authentication
- Per-user credentials
- CORS restrictions
- HTTPS/TLS
- Rate limiting
- Audit logging

## Future Architecture Enhancements

### Planned Improvements
- [ ] WebSocket support for real-time transcript push
- [ ] Database persistence (PostgreSQL/SQLite)
- [ ] User authentication and sessions
- [ ] Web frontend (React/Vue)
- [ ] CLI client
- [ ] Mobile app
- [ ] Kubernetes deployment
- [ ] API versioning (`/api/v1/...`)
- [ ] OpenAPI 3.0 schema generation

### Plugin System (Future)
```
backend/
└── plugins/
    ├── custom_llm_provider.py
    ├── custom_transcription_service.py
    └── custom_storage_backend.py
```

## Development Setup

### Backend Development
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
python main.py
# Visit http://localhost:8000/docs for API testing
```

### Frontend Development
```bash
cd frontend_v3
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export DNA_BACKEND_URL=http://localhost:8000
export DNA_DEBUG=true
python main.py
```

### Creating a New Frontend
```python
# example_client.py
import requests

class DNAClient:
    def __init__(self, backend_url="http://localhost:8000"):
        self.base_url = backend_url
    
    def health_check(self):
        response = requests.get(f"{self.base_url}/health")
        return response.json()
    
    # Add more API calls as needed...

# Use it
client = DNAClient("http://localhost:8000")
health = client.health_check()
print(health["status"])  # "healthy"
```

See [`backend/example_client.py`](backend/example_client.py) for a complete example.

## Testing

### Backend Testing
```bash
# Test health endpoint
curl http://localhost:8000/health

# Test version creation
curl -X POST http://localhost:8000/versions \
  -H "Content-Type: application/json" \
  -d '{"version_id": "TEST_001", "description": "Test version"}'

# View interactive docs
open http://localhost:8000/docs
```

### Frontend Testing
```bash
# Test with custom backend URL
export DNA_BACKEND_URL=http://dev-server:8000
python main.py

# Enable debug logging
export DNA_DEBUG=true
python main.py
```

## Conclusion

The DNA Dailies Notes Assistant uses a clean, decoupled architecture that separates frontend and backend concerns. This design:

✅ Allows multiple frontend implementations  
✅ Enables independent backend deployment  
✅ Facilitates testing and development  
✅ Supports future scalability  
✅ Maintains simple local desktop use case  

The backend is a standalone REST API that can serve any HTTP client, making it flexible for current needs and future expansion.
