# DNA Dailies Notes Assistant - Qt Desktop App

Qt/QML desktop application for dailies review with real-time transcription.

## Setup

1. **Create virtual environment** (if not already done):
```bash
python3.12 -m venv venv
source venv/bin/activate
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

## Running the App

1. **Start the backend server** (in a separate terminal):
```bash
cd ../backend
source venv/bin/activate
python main.py
```

2. **Run the Qt app**:
```bash
source venv/bin/activate
python main.py
```

## Project Structure

```
frontend_v2/
├── main.py                  # Application entry point
├── models/                  # Qt data models
│   └── version_list_model.py
├── services/                # Backend communication
│   └── backend_service.py
├── ui/                      # QML UI files
│   └── main.qml
└── venv/                    # Virtual environment
```

## Features

- ✅ Version list with selection
- ✅ User Notes with staging/send workflow
- ✅ AI Notes generation (test output)
- ✅ Transcript display
- ✅ Name prompt on first launch
- ✅ Dark theme matching web version

## Next Steps

- [ ] Connect to real backend API
- [ ] WebSocket for real-time transcripts
- [ ] ShotGrid playlist loading
- [ ] CSV import/export
- [ ] LLM assistant integration
- [ ] Packaging for distribution
