# DNA Application Startup Guide

## Architecture Overview

The DNA application now uses a **backend-first architecture**:
- **Backend**: FastAPI server (Python) that manages all data
- **Frontend**: Qt/QML desktop application that communicates with backend via REST API

**IMPORTANT**: The backend MUST be running before starting the frontend.

---

## Starting the Application

### Step 1: Start the Backend Server

```bash
cd /Users/cameronbriantarget/Local/VFXOpenSource/dna/experimental/cameron/backend
source venv/bin/activate
python -m uvicorn main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
OpenAI client initialized successfully
INFO:     Application startup complete.
```

**Keep this terminal window open** - the backend must keep running.

### Step 2: Start the Frontend Application

Open a NEW terminal window:

```bash
cd /Users/cameronbriantarget/Local/VFXOpenSource/dna/experimental/cameron/frontend_v2
python3 main.py
```

You should see:
```
✓ Connected to backend at http://localhost:8000
```

If you see an error about backend connection, make sure Step 1 is complete.

---

## Backend API Endpoints

The backend provides these endpoints:

### Version Management
- `POST /versions/upload-csv` - Upload CSV to create versions
- `GET /versions` - Get all versions
- `GET /versions/{version_id}` - Get specific version
- `POST /versions/{version_id}/notes` - Add note to version
- `PUT /versions/{version_id}/notes` - Update version notes
- `POST /versions/{version_id}/generate-ai-notes` - Generate AI notes
- `GET /versions/export/csv` - Export versions to CSV
- `DELETE /versions/{version_id}` - Delete version
- `DELETE /versions` - Clear all versions

### LLM Integration
- `POST /llm-summary` - Generate AI summary from text

### Email
- `POST /email-notes` - Send notes via email

### ShotGrid
- Various ShotGrid endpoints (if configured)

---

## Testing the Backend

You can test the backend API directly with curl:

```bash
# Check if backend is running
curl http://localhost:8000/config

# Upload a CSV
curl -X POST -F "file=@/path/to/versions.csv" http://localhost:8000/versions/upload-csv

# Get all versions
curl http://localhost:8000/versions

# Add a note
curl -X POST http://localhost:8000/versions/{version_id}/notes \
  -H "Content-Type: application/json" \
  -d '{"version_id": "1001", "note_text": "Great shot!"}'

# Export CSV
curl http://localhost:8000/versions/export/csv -o export.csv
```

---

## CSV Format

When importing CSVs, use this format:

```csv
Version Name,ID
shot_010_v001,1001
shot_020_v001,1002
shot_030_v001,1003
```

- **First column**: Version Name (REQUIRED) - always the leftmost column
- **ID column**: Optional Version ID - only if CSV has "ID" header
- **Header row**: Always included and automatically skipped

---

## Features

### ✅ Working
- CSV import/export
- Version selection and switching
- User notes per version (persistent)
- AI notes generation
- Backend API integration
- Real-time updates

### 🚧 To Be Implemented
- Meeting functionality
- ShotGrid integration (if enabled)
- Transcript capture
- Email notifications

---

## Troubleshooting

### "Cannot connect to backend"
- Make sure backend is running (Step 1)
- Check that port 8000 is not in use: `lsof -i :8000`
- Verify backend URL in frontend: should be `http://localhost:8000`

### "No module named 'uvicorn'"
- Activate the virtual environment: `source venv/bin/activate`
- Or install dependencies: `pip install -r requirements.txt`

### "No module named 'PySide6'"
- Install PySide6 for frontend: `pip install PySide6`

### Backend crashes or errors
- Check the backend terminal for error messages
- Verify all dependencies are installed
- Check `.env` file for required configuration

---

## Development Notes

- Backend stores versions **in memory** (not persistent across restarts)
- To make persistent, add database integration (SQLite, PostgreSQL, etc.)
- Frontend has NO local storage - all data comes from backend
- Backend must be running for frontend to function
