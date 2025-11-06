# Merged DNA Application

A unified DNA (Dailies Note Assistant) application that combines the best of both ILM's frontend framework approach and SPI's full-stack application features.

## Architecture Overview

This merged application consists of three main components:

```
merged-dna-app/
├── backend/          # FastAPI backend from SPI
├── frontend/         # React frontend using ILM framework + SPI features
└── shared/           # Reusable DNA frontend framework library
    └── dna-frontend-framework/
```

### Key Features

**From ILM:**
- Clean, reusable TypeScript framework architecture
- Abstract interfaces for transcription agents and LLM providers
- Centralized state management with observer pattern
- Modern React with Radix UI components
- Comprehensive type safety

**From SPI:**
- Full FastAPI backend with multiple services
- Email integration via Gmail API
- **ShotGrid integration** - Load playlists and shots directly from ShotGrid (optional)
- Multiple LLM provider support (OpenAI, Claude, Gemini, Ollama)
- CSV playlist upload functionality

**Merged Benefits:**
- Best-in-class frontend framework with production-ready backend
- Clean separation of concerns
- Extensible and maintainable codebase
- **Seamless ShotGrid integration** in the UI with project/playlist selectors
- Ready for deployment

## Prerequisites

- Node.js 18+ and npm
- Python 3.8+
- Vexa API access (for transcription)
- LLM API key (OpenAI, Gemini, Claude, or Ollama)
- Gmail API credentials (optional, for email features)
- ShotGrid credentials (optional, for ShotGrid integration)

## Setup Instructions

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys and configuration

# Start backend server
uvicorn main:app --reload --port 8000
```

**Backend Environment Variables (.env):**
```
# ShotGrid (Optional)
SHOTGRID_URL=https://your-studio.shotgunstudio.com
SHOTGRID_SCRIPT_NAME=your-script-name
SHOTGRID_API_KEY=your-api-key
DEMO_MODE=false

# Gmail (Required for email features)
GMAIL_SENDER=your-email@gmail.com

# LLM API Keys (at least one required)
GEMINI_API_KEY=your-gemini-api-key
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key

# Testing
DISABLE_LLM=false
```

### 2. Shared Framework Setup

```bash
cd shared/dna-frontend-framework

# Install dependencies
npm install

# Build the framework
npm run build
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Edit .env with your configuration

# Start development server
npm run dev
```

**Frontend Environment Variables (.env):**
```
# Vexa Configuration
VITE_VEXA_API_KEY=your-vexa-api-key
VITE_VEXA_URL=http://localhost:18056
VITE_PLATFORM=google_meet

# LLM Configuration
VITE_LLM_INTERFACE=litellm
VITE_LLM_MODEL=gemini-2.5-pro
VITE_LLM_BASEURL=https://api.openai.com/v1
VITE_LLM_API_KEY=your-llm-api-key

# Backend URL
VITE_BACKEND_URL=http://localhost:8000
```

## Usage

1. **Start the Backend:**
   ```bash
   cd backend
   source venv/bin/activate
   uvicorn main:app --reload --port 8000
   ```

2. **Start the Frontend:**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Access the Application:**
   Open http://localhost:5173 in your browser

4. **Join a Meeting:**
   - Enter a Google Meet URL or ID in the "Meeting ID" field
   - Click "Join Meeting" to start transcription
   - The status badge will show connection status

5. **Manage Notes:**
   - Each version card shows:
     - User Notes (editable)
     - AI Generated Notes (read-only)
     - Live Transcript (read-only)
   - Click "Generate AI Notes" to create AI summaries
   - Click "Add to Notes" to merge AI notes into user notes

6. **Email Notes:**
   - Enter recipient email address
   - Click "Send Notes via Email" to send formatted HTML table
   - Notes include all versions with user notes, transcripts, and AI summaries

## Project Structure

### Backend (`backend/`)

- `main.py` - FastAPI app initialization and routing
- `note_service.py` - LLM summarization service
- `email_service.py` - Gmail integration
- `playlist.py` - CSV upload handler
- `shotgrid_service.py` - ShotGrid integration (optional)

**API Endpoints:**
- `POST /llm-summary` - Generate AI summary from transcript
- `POST /email-notes` - Send notes via Gmail
- `POST /upload-playlist` - Upload shot list CSV
- `GET /projects` - Get ShotGrid projects (if enabled)
- `GET /projects/{id}/playlists` - Get project playlists (if enabled)

### Frontend (`frontend/`)

```
frontend/
├── src/
│   ├── App.tsx              # Main application component
│   ├── main.tsx             # React entry point
│   ├── hooks/
│   │   ├── useDNAFramework.ts    # Framework initialization hook
│   │   └── useGetVersions.ts     # Version data hook
│   └── lib/
│       ├── bot-service.ts        # Vexa bot management
│       ├── websocket-service.ts  # WebSocket handling
│       ├── transcription-service.ts  # Transcription API client
│       ├── types.ts              # TypeScript types
│       └── config.ts             # Configuration
├── vite.config.ts
├── tsconfig.json
└── package.json
```

### Shared Framework (`shared/dna-frontend-framework/`)

```
dna-frontend-framework/
├── index.ts                 # Main DNAFrontendFramework class
├── types.ts                 # Core type definitions
├── state/
│   └── stateManager.ts     # State management with observer pattern
├── transcription/
│   ├── transcriptionAgent.ts          # Abstract base class
│   └── vexa/
│       └── vexaTranscriptionAgent.ts  # Vexa implementation
└── notes/
    ├── noteGenerator.ts    # LLM orchestration
    ├── prompt.ts          # System prompts
    └── LLMs/
        ├── llmInterface.ts      # Abstract LLM interface
        ├── openAiInterface.ts   # OpenAI implementation
        └── liteLlm.ts          # LiteLLM implementation
```

## Development

### Building the Framework

After making changes to the shared framework:

```bash
cd shared/dna-frontend-framework
npm run build
```

The frontend will automatically use the updated framework.

### Running Tests

Framework tests:
```bash
cd shared/dna-frontend-framework
npm test
```

### Linting

Frontend linting:
```bash
cd frontend
npm run lint
```

## Troubleshooting

### Backend Won't Start

- Verify Python virtual environment is activated
- Check all required environment variables are set in `.env`
- Ensure port 8000 is not in use

### Frontend Build Errors

- Rebuild the framework: `cd shared/dna-frontend-framework && npm run build`
- Clear node_modules: `rm -rf node_modules package-lock.json && npm install`

### Connection Errors

- Verify Vexa server URL is correct and accessible
- Check that backend is running on http://localhost:8000
- Ensure CORS is properly configured in backend

### Email Not Sending

- Verify Gmail API credentials are set up (requires `client_secret.json`)
- Check that Gmail sender email is configured in `.env`
- Run OAuth flow to authorize the application

## Gmail API Setup (Optional)

To enable email functionality:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Gmail API
4. Create OAuth 2.0 credentials (Desktop app)
5. Download credentials as `client_secret.json`
6. Place in `backend/` directory
7. Run the app - it will prompt for authorization on first use

## ShotGrid Setup (Optional)

To enable ShotGrid integration:

1. Create a ShotGrid script user
2. Generate API key
3. Configure environment variables:
   ```
   SHOTGRID_URL=https://your-studio.shotgunstudio.com
   SHOTGRID_SCRIPT_NAME=your-script-name
   SHOTGRID_API_KEY=your-api-key
   ```

## Configuration Options

### LLM Providers

The application supports multiple LLM providers:

- **OpenAI**: Set `VITE_LLM_INTERFACE=openai` and `OPENAI_API_KEY`
- **LiteLLM**: Set `VITE_LLM_INTERFACE=litellm` for proxy support
- **Gemini**: Backend uses Gemini by default with `GEMINI_API_KEY`
- **Claude**: Backend supports via `ANTHROPIC_API_KEY`
- **Ollama**: Backend supports local Ollama instance

### Platform Support

Currently supports Google Meet (`VITE_PLATFORM=google_meet`). Microsoft Teams support can be added via Vexa configuration.

## Contributing

When contributing to this merged application:

1. Keep framework code in `shared/dna-frontend-framework/`
2. Keep application-specific code in `frontend/` and `backend/`
3. Maintain TypeScript type safety
4. Write tests for new framework features
5. Update this README with new features or setup steps

## License

[Add your license here]

## Support

For issues or questions:
- Check the troubleshooting section
- Review logs in browser console (F12) and backend terminal
- Verify all environment variables are correctly set
