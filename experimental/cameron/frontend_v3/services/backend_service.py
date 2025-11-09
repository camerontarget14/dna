"""
Backend API Service
Handles communication with the FastAPI backend server
ONLY uses backend API - no local storage
"""

import requests
from PySide6.QtCore import Property, QObject, QTimer, Signal, Slot

from services.vexa_service import VexaService


class BackendService(QObject):
    """Service for communicating with the backend API"""

    # Signals for property changes
    userNameChanged = Signal()
    meetingIdChanged = Signal()
    selectedVersionIdChanged = Signal()
    selectedVersionNameChanged = Signal()
    currentNotesChanged = Signal()
    currentAiNotesChanged = Signal()
    currentTranscriptChanged = Signal()
    stagingNoteChanged = Signal()
    currentVersionNoteChanged = Signal()

    # LLM API Keys and Prompts
    openaiApiKeyChanged = Signal()
    openaiPromptChanged = Signal()
    claudeApiKeyChanged = Signal()
    claudePromptChanged = Signal()
    geminiApiKeyChanged = Signal()
    geminiPromptChanged = Signal()

    # ShotGrid
    shotgridProjectsChanged = Signal()
    shotgridPlaylistsChanged = Signal()
    shotgridWebUrlChanged = Signal()
    shotgridApiKeyChanged = Signal()
    shotgridScriptNameChanged = Signal()

    # Versions
    versionsLoaded = Signal()

    # Vexa/Meeting signals
    meetingStatusChanged = Signal()
    vexaApiKeyChanged = Signal()
    vexaApiUrlChanged = Signal()

    def __init__(self, backend_url="http://localhost:8000"):
        super().__init__()
        self._backend_url = backend_url
        self._check_backend_connection()

        # User info
        self._user_name = ""
        self._meeting_id = ""

        # Vexa integration
        self._vexa_api_key = ""
        self._vexa_api_url = "https://devapi.dev.vexa.ai"
        self._vexa_service = None
        self._meeting_active = False
        self._meeting_status = (
            "disconnected"  # disconnected, connecting, connected, error
        )
        self._current_meeting_id = ""
        self._transcription_timer = None

        # Current version
        self._selected_version_id = None
        self._selected_version_name = ""

        # Notes and transcript
        self._current_notes = ""
        self._current_ai_notes = ""
        self._current_transcript = ""
        self._staging_note = ""

        # LLM settings
        self._openai_api_key = ""
        self._openai_prompt = ""
        self._claude_api_key = ""
        self._claude_prompt = ""
        self._gemini_api_key = ""
        self._gemini_prompt = ""

        # ShotGrid
        self._shotgrid_projects = []
        self._shotgrid_playlists = []
        self._shotgrid_projects_data = []
        self._shotgrid_playlists_data = []
        self._selected_playlist_id = None
        self._shotgrid_web_url = ""
        self._shotgrid_api_key = ""
        self._shotgrid_script_name = ""

        # Per-version notes storage (version_id -> note_text)
        self._version_notes = {}
        self._current_version_note = ""

        # Check if ShotGrid is enabled and load projects
        self._check_shotgrid_enabled()

    def _check_backend_connection(self):
        """Check if backend is running"""
        try:
            response = requests.get(f"{self._backend_url}/config", timeout=2)
            if response.status_code == 200:
                print(f"✓ Connected to backend at {self._backend_url}")
                return True
        except requests.exceptions.RequestException as e:
            print(f"✗ ERROR: Cannot connect to backend at {self._backend_url}")
            print(f"  Please start the backend server first!")
            print(f"  Error: {e}")
            return False

    def _check_shotgrid_enabled(self):
        """Check if ShotGrid is enabled and load projects if it is"""
        try:
            response = requests.get(f"{self._backend_url}/config", timeout=2)
            if response.status_code == 200:
                data = response.json()
                shotgrid_enabled = data.get("shotgrid_enabled", False)
                if shotgrid_enabled:
                    print("✓ ShotGrid is enabled, loading projects...")
                    self.loadShotGridProjects()
                else:
                    print("ShotGrid is not enabled")
        except Exception as e:
            print(f"Could not check ShotGrid status: {e}")

    def _make_request(self, method, endpoint, **kwargs):
        """Make a request to the backend API with error handling"""
        url = f"{self._backend_url}{endpoint}"
        try:
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"ERROR: API request failed: {method} {endpoint}")
            print(f"  Error: {e}")
            raise

    # ===== User Properties =====

    @Property(str, notify=userNameChanged)
    def userName(self):
        return self._user_name

    @userName.setter
    def userName(self, value):
        if self._user_name != value:
            self._user_name = value
            self.userNameChanged.emit()

    @Property(str, notify=meetingIdChanged)
    def meetingId(self):
        return self._meeting_id

    @meetingId.setter
    def meetingId(self, value):
        if self._meeting_id != value:
            self._meeting_id = value
            self.meetingIdChanged.emit()

    # ===== Version Properties =====

    @Property(str, notify=selectedVersionIdChanged)
    def selectedVersionId(self):
        return self._selected_version_id if self._selected_version_id else ""

    @Property(str, notify=selectedVersionNameChanged)
    def selectedVersionName(self):
        return self._selected_version_name

    @Property(str, notify=currentNotesChanged)
    def currentNotes(self):
        return self._current_notes

    @Property(str, notify=currentAiNotesChanged)
    def currentAiNotes(self):
        return self._current_ai_notes

    @Property(str, notify=currentTranscriptChanged)
    def currentTranscript(self):
        return self._current_transcript

    @Property(str, notify=stagingNoteChanged)
    def stagingNote(self):
        return self._staging_note

    @stagingNote.setter
    def stagingNote(self, value):
        if self._staging_note != value:
            self._staging_note = value
            self.stagingNoteChanged.emit()

    @Property(str, notify=currentVersionNoteChanged)
    def currentVersionNote(self):
        return self._current_version_note

    # ===== LLM Properties =====

    @Property(str, notify=openaiApiKeyChanged)
    def openaiApiKey(self):
        return self._openai_api_key

    @openaiApiKey.setter
    def openaiApiKey(self, value):
        if self._openai_api_key != value:
            self._openai_api_key = value
            self.openaiApiKeyChanged.emit()

    @Property(str, notify=openaiPromptChanged)
    def openaiPrompt(self):
        return self._openai_prompt

    @openaiPrompt.setter
    def openaiPrompt(self, value):
        if self._openai_prompt != value:
            self._openai_prompt = value
            self.openaiPromptChanged.emit()

    @Property(str, notify=claudeApiKeyChanged)
    def claudeApiKey(self):
        return self._claude_api_key

    @claudeApiKey.setter
    def claudeApiKey(self, value):
        if self._claude_api_key != value:
            self._claude_api_key = value
            self.claudeApiKeyChanged.emit()

    @Property(str, notify=claudePromptChanged)
    def claudePrompt(self):
        return self._claude_prompt

    @claudePrompt.setter
    def claudePrompt(self, value):
        if self._claude_prompt != value:
            self._claude_prompt = value
            self.claudePromptChanged.emit()

    @Property(str, notify=geminiApiKeyChanged)
    def geminiApiKey(self):
        return self._gemini_api_key

    @geminiApiKey.setter
    def geminiApiKey(self, value):
        if self._gemini_api_key != value:
            self._gemini_api_key = value
            self.geminiApiKeyChanged.emit()

    @Property(str, notify=geminiPromptChanged)
    def geminiPrompt(self):
        return self._gemini_prompt

    @geminiPrompt.setter
    def geminiPrompt(self, value):
        if self._gemini_prompt != value:
            self._gemini_prompt = value
            self.geminiPromptChanged.emit()

    # ===== Version Management =====

    def fetch_versions(self):
        """Fetch versions from backend API"""
        try:
            response = self._make_request("GET", "/versions")
            data = response.json()

            versions = data.get("versions", [])
            print(f"Fetched {len(versions)} versions from backend")

            # Convert to format expected by model
            return [{"id": v["id"], "description": v["name"]} for v in versions]
        except Exception as e:
            print(f"ERROR: Failed to fetch versions: {e}")
            return []

    @Slot(str)
    def selectVersion(self, version_id):
        """Select a version and load its data from backend"""
        print(f"\nSelecting version: {version_id}")

        try:
            response = self._make_request("GET", f"/versions/{version_id}")
            data = response.json()
            version = data.get("version", {})

            # Update selected version
            self._selected_version_id = version.get("id", "")
            self._selected_version_name = version.get("name", "")

            # Load notes and transcript
            self._current_notes = version.get("user_notes", "")
            self._current_ai_notes = version.get("ai_notes", "")
            self._current_transcript = version.get("transcript", "")

            # Load per-version note
            self._current_version_note = self._version_notes.get(version_id, "")

            # Clear staging
            self._staging_note = ""

            # Emit signals
            self.selectedVersionIdChanged.emit()
            self.selectedVersionNameChanged.emit()
            self.currentNotesChanged.emit()
            self.currentAiNotesChanged.emit()
            self.currentTranscriptChanged.emit()
            self.currentVersionNoteChanged.emit()
            self.stagingNoteChanged.emit()

            print(f"✓ Loaded version '{self._selected_version_name}'")
            print(f"  User notes: {len(self._current_notes)} chars")
            print(f"  AI notes: {len(self._current_ai_notes)} chars")
            print(f"  Version note: {len(self._current_version_note)} chars")

        except Exception as e:
            print(f"ERROR: Failed to select version: {e}")

    @Slot(str)
    def saveNoteToVersion(self, note_text):
        """Save a note to the currently selected version via backend API"""
        if not note_text.strip():
            print("Note text is empty, not saving")
            return

        if not self._selected_version_id:
            print("ERROR: No version selected")
            return

        print(
            f"Saving note to version '{self._selected_version_name}': {note_text[:50]}..."
        )

        try:
            response = self._make_request(
                "POST",
                f"/versions/{self._selected_version_id}/notes",
                json={"version_id": self._selected_version_id, "note_text": note_text},
            )

            data = response.json()
            version = data.get("version", {})

            # Update current notes from backend response
            self._current_notes = version.get("user_notes", "")
            self.currentNotesChanged.emit()

            # Clear staging
            self._staging_note = ""
            self.stagingNoteChanged.emit()

            print(f"✓ Note saved successfully")

        except Exception as e:
            print(f"ERROR: Failed to save note: {e}")

    @Slot()
    def generateNotes(self):
        """Generate AI notes for the current version"""
        if not self._selected_version_id:
            print("ERROR: No version selected")
            return

        if not self._current_transcript:
            print("ERROR: No transcript available for AI note generation")
            return

        print(f"Generating AI notes for version '{self._selected_version_name}'...")

        try:
            response = self._make_request(
                "POST",
                f"/versions/{self._selected_version_id}/generate-ai-notes",
                json={
                    "version_id": self._selected_version_id,
                    "transcript": self._current_transcript,
                },
            )

            data = response.json()
            version = data.get("version", {})

            # Update AI notes from backend response
            self._current_ai_notes = version.get("ai_notes", "")
            self.currentAiNotesChanged.emit()

            print(f"✓ AI notes generated successfully")

        except Exception as e:
            print(f"ERROR: Failed to generate AI notes: {e}")

    @Slot()
    def addAiNotesToStaging(self):
        """Add AI notes to the current version's note entry"""
        # Get the AI notes text (even if it's placeholder text from the UI)
        ai_text = self._current_ai_notes if self._current_ai_notes else ""

        # Add to current version note (append if there's existing text)
        if self._current_version_note and self._current_version_note.strip():
            self._current_version_note = self._current_version_note + "\n\n" + ai_text
        else:
            self._current_version_note = ai_text

        # Update storage
        if self._selected_version_id:
            self._version_notes[self._selected_version_id] = self._current_version_note

        self.currentVersionNoteChanged.emit()
        print(f"Added AI notes to version note: {len(ai_text)} chars")

    @Slot(str)
    def addAiNotesText(self, text):
        """Add specific text (from AI notes area) to the current version's note entry"""
        # Add to current version note (append if there's existing text)
        if self._current_version_note and self._current_version_note.strip():
            self._current_version_note = self._current_version_note + "\n\n" + text
        else:
            self._current_version_note = text

        # Update storage
        if self._selected_version_id:
            self._version_notes[self._selected_version_id] = self._current_version_note

        self.currentVersionNoteChanged.emit()
        print(f"Added text to version note: {len(text)} chars")

    @Slot(str)
    def updateVersionNote(self, note_text):
        """Update the note for the current version (stored locally per-version)"""
        if not self._selected_version_id:
            return

        # Store note for this version
        self._version_notes[self._selected_version_id] = note_text
        self._current_version_note = note_text
        self.currentVersionNoteChanged.emit()

    @Slot()
    def captureScreenshot(self):
        """Capture a screenshot (placeholder for now)"""
        print("📷 Screenshot capture requested")
        # TODO: Implement screenshot capture functionality

    @Slot()
    def resetWorkspace(self):
        """Reset workspace - clear all versions and notes"""
        print("Resetting workspace...")

        try:
            # Clear all versions via backend API
            response = self._make_request("DELETE", "/versions")

            # Clear local state
            self._selected_version_id = None
            self._selected_version_name = ""
            self._current_notes = ""
            self._current_ai_notes = ""
            self._current_transcript = ""
            self._staging_note = ""
            self._current_version_note = ""
            self._version_notes.clear()

            # Emit signals to update UI
            self.selectedVersionIdChanged.emit()
            self.selectedVersionNameChanged.emit()
            self.currentNotesChanged.emit()
            self.currentAiNotesChanged.emit()
            self.currentTranscriptChanged.emit()
            self.stagingNoteChanged.emit()
            self.currentVersionNoteChanged.emit()
            self.versionsLoaded.emit()

            print("✓ Workspace reset successfully")

        except Exception as e:
            print(f"ERROR: Failed to reset workspace: {e}")

    # ===== Vexa/Meeting Integration =====

    @Property(str, notify=vexaApiKeyChanged)
    def vexaApiKey(self):
        return self._vexa_api_key

    @vexaApiKey.setter
    def vexaApiKey(self, value):
        if self._vexa_api_key != value:
            self._vexa_api_key = value
            self.vexaApiKeyChanged.emit()
            # Reinitialize Vexa service with new key
            if value:
                self._vexa_service = VexaService(value, self._vexa_api_url)

    @Property(str, notify=vexaApiUrlChanged)
    def vexaApiUrl(self):
        return self._vexa_api_url

    @vexaApiUrl.setter
    def vexaApiUrl(self, value):
        if self._vexa_api_url != value:
            self._vexa_api_url = value
            self.vexaApiUrlChanged.emit()
            # Reinitialize Vexa service with new URL
            if self._vexa_api_key:
                self._vexa_service = VexaService(self._vexa_api_key, value)

    @Property(bool, notify=meetingStatusChanged)
    def meetingActive(self):
        return self._meeting_active

    @Property(str, notify=meetingStatusChanged)
    def meetingStatus(self):
        return self._meeting_status

    @Slot()
    def joinMeeting(self):
        """Join a meeting and start transcription"""
        if not self._meeting_id or not self._vexa_api_key:
            print("ERROR: Meeting ID or Vexa API key not set")
            self._meeting_status = "error"
            self.meetingStatusChanged.emit()
            return

        if not self._vexa_service:
            self._vexa_service = VexaService(self._vexa_api_key, self._vexa_api_url)

        # Set status to connecting
        self._meeting_status = "connecting"
        self.meetingStatusChanged.emit()

        try:
            print(f"\n=== Joining Meeting ===")
            print(f"Meeting URL/ID: {self._meeting_id}")

            result = self._vexa_service.start_transcription(
                self._meeting_id, language="auto", bot_name="DNA Assistant"
            )

            if result.get("success"):
                self._current_meeting_id = result.get("meeting_id", self._meeting_id)
                self._meeting_active = True
                self._meeting_status = "connected"
                self.meetingStatusChanged.emit()

                print(f"✓ Successfully joined meeting")
                print(f"  Internal meeting ID: {self._current_meeting_id}")

                # Start polling for transcription updates
                self._start_transcription_polling()
            else:
                print(f"ERROR: Failed to join meeting")
                self._meeting_status = "error"
                self.meetingStatusChanged.emit()

        except Exception as e:
            print(f"ERROR: Failed to join meeting: {e}")
            self._meeting_active = False
            self._meeting_status = "error"
            self.meetingStatusChanged.emit()

    @Slot()
    def leaveMeeting(self):
        """Leave the current meeting and stop transcription"""
        if not self._current_meeting_id:
            print("ERROR: No active meeting")
            return

        if not self._vexa_service:
            print("ERROR: Vexa service not initialized")
            return

        try:
            print(f"\n=== Leaving Meeting ===")
            print(f"Meeting ID: {self._current_meeting_id}")

            result = self._vexa_service.stop_transcription(self._current_meeting_id)

            if result.get("success"):
                print(f"✓ Successfully left meeting")

                # Stop polling
                self._stop_transcription_polling()

                self._meeting_active = False
                self._meeting_status = "disconnected"
                self._current_meeting_id = ""
                self.meetingStatusChanged.emit()
            else:
                print(f"ERROR: Failed to leave meeting")
                self._meeting_status = "error"
                self.meetingStatusChanged.emit()

        except Exception as e:
            print(f"ERROR: Failed to leave meeting: {e}")
            self._meeting_status = "error"
            self.meetingStatusChanged.emit()

    @Slot(str)
    def updateTranscriptionLanguage(self, language):
        """Update the transcription language"""
        if not self._current_meeting_id:
            print("ERROR: No active meeting")
            return

        if not self._vexa_service:
            print("ERROR: Vexa service not initialized")
            return

        try:
            print(f"Updating transcription language to: {language}")
            result = self._vexa_service.update_language(
                self._current_meeting_id, language
            )

            if result.get("success"):
                print(f"✓ Language updated successfully")
            else:
                print(f"ERROR: Failed to update language")

        except Exception as e:
            print(f"ERROR: Failed to update language: {e}")

    def _start_transcription_polling(self):
        """Start polling for transcription updates"""
        if self._transcription_timer:
            self._transcription_timer.stop()

        self._transcription_timer = QTimer()
        self._transcription_timer.timeout.connect(self._poll_transcription)
        self._transcription_timer.start(5000)  # Poll every 5 seconds

        print("Started transcription polling (every 5 seconds)")

        # Do initial fetch
        self._poll_transcription()

    def _stop_transcription_polling(self):
        """Stop polling for transcription updates"""
        if self._transcription_timer:
            self._transcription_timer.stop()
            self._transcription_timer = None
            print("Stopped transcription polling")

    def _poll_transcription(self):
        """Poll for transcription updates"""
        if not self._current_meeting_id or not self._vexa_service:
            return

        try:
            transcription_data = self._vexa_service.get_transcription(
                self._current_meeting_id
            )

            # Update transcript
            segments = transcription_data.segments
            if segments:
                # Combine all segment texts into full transcript
                full_text = "\n".join(
                    [
                        f"{seg.get('speaker', 'Unknown')}: {seg.get('text', '')}"
                        for seg in segments
                    ]
                )

                if full_text != self._current_transcript:
                    self._current_transcript = full_text
                    self.currentTranscriptChanged.emit()
                    print(
                        f"Transcript updated: {len(segments)} segments, {len(full_text)} chars"
                    )

        except Exception as e:
            # Don't spam errors, transcription might not be ready yet
            pass

    # ===== CSV Import/Export =====

    @Slot(str)
    def importCSV(self, file_url):
        """Import versions from CSV via backend API"""
        # Convert file URL to path
        file_path = file_url.replace("file://", "")

        print(f"Importing CSV: {file_path}")

        try:
            with open(file_path, "rb") as f:
                files = {"file": ("playlist.csv", f, "text/csv")}
                response = requests.post(
                    f"{self._backend_url}/versions/upload-csv", files=files
                )
                response.raise_for_status()

            data = response.json()
            count = data.get("count", 0)

            print(f"✓ Imported {count} versions from CSV")

            # Emit signal to reload versions
            self.versionsLoaded.emit()

        except Exception as e:
            print(f"ERROR: Failed to import CSV: {e}")

    @Slot(str)
    def exportCSV(self, file_url):
        """Export versions to CSV via backend API"""
        # Convert file URL to path
        file_path = file_url.replace("file://", "")

        print(f"Exporting CSV: {file_path}")

        try:
            response = self._make_request("GET", "/versions/export/csv")

            # Write response content to file
            with open(file_path, "wb") as f:
                f.write(response.content)

            print(f"✓ Exported versions to CSV: {file_path}")

        except Exception as e:
            print(f"ERROR: Failed to export CSV: {e}")

    # ===== ShotGrid Integration =====

    @Property(list, notify=shotgridProjectsChanged)
    def shotgridProjects(self):
        return self._shotgrid_projects

    @Property(list, notify=shotgridPlaylistsChanged)
    def shotgridPlaylists(self):
        return self._shotgrid_playlists

    @Property(str, notify=shotgridWebUrlChanged)
    def shotgridWebUrl(self):
        return self._shotgrid_web_url

    @shotgridWebUrl.setter
    def shotgridWebUrl(self, value):
        if self._shotgrid_web_url != value:
            self._shotgrid_web_url = value
            self.shotgridWebUrlChanged.emit()
            print(f"ShotGrid Web URL updated: {value}")

    @Property(str, notify=shotgridApiKeyChanged)
    def shotgridApiKey(self):
        return self._shotgrid_api_key

    @shotgridApiKey.setter
    def shotgridApiKey(self, value):
        if self._shotgrid_api_key != value:
            self._shotgrid_api_key = value
            self.shotgridApiKeyChanged.emit()
            print("ShotGrid API Key updated")

    @Property(str, notify=shotgridScriptNameChanged)
    def shotgridScriptName(self):
        return self._shotgrid_script_name

    @shotgridScriptName.setter
    def shotgridScriptName(self, value):
        if self._shotgrid_script_name != value:
            self._shotgrid_script_name = value
            self.shotgridScriptNameChanged.emit()
            print(f"ShotGrid Script Name updated: {value}")

    @Slot()
    def loadShotGridProjects(self):
        """Load ShotGrid projects from backend API"""
        print("Loading ShotGrid projects...")

        try:
            response = self._make_request("GET", "/shotgrid/active-projects")
            data = response.json()

            if data.get("status") == "success":
                projects = data.get("projects", [])
                # Convert to QML-friendly format (list of strings showing project code)
                self._shotgrid_projects = [
                    f"{p['code']} (ID: {p['id']})" for p in projects
                ]
                # Store full project data for later use
                self._shotgrid_projects_data = projects
                self.shotgridProjectsChanged.emit()

                print(f"✓ Loaded {len(projects)} ShotGrid projects")
            else:
                print(f"ERROR: Failed to load projects: {data.get('message')}")
                self._shotgrid_projects = []
                self._shotgrid_projects_data = []
                self.shotgridProjectsChanged.emit()

        except Exception as e:
            print(f"ERROR: Failed to load ShotGrid projects: {e}")
            self._shotgrid_projects = []
            self._shotgrid_projects_data = []
            self.shotgridProjectsChanged.emit()

    @Slot(int)
    def selectShotgridProject(self, index):
        """Select a ShotGrid project by index and load its playlists"""
        if (
            not hasattr(self, "_shotgrid_projects_data")
            or index < 0
            or index >= len(self._shotgrid_projects_data)
        ):
            print(f"ERROR: Invalid project index: {index}")
            return

        project = self._shotgrid_projects_data[index]
        project_id = project["id"]
        print(f"Selected ShotGrid project: {project['code']} (ID: {project_id})")

        # Load playlists for this project
        self.loadShotGridPlaylists(project_id)

    @Slot(int)
    def loadShotGridPlaylists(self, project_id):
        """Load ShotGrid playlists for a project"""
        print(f"Loading ShotGrid playlists for project ID: {project_id}")

        try:
            response = self._make_request(
                "GET", f"/shotgrid/latest-playlists/{project_id}"
            )
            data = response.json()

            if data.get("status") == "success":
                playlists = data.get("playlists", [])
                # Convert to QML-friendly format
                self._shotgrid_playlists = [
                    f"{p['code']} (ID: {p['id']})" for p in playlists
                ]
                # Store full playlist data for later use
                self._shotgrid_playlists_data = playlists
                self.shotgridPlaylistsChanged.emit()

                print(f"✓ Loaded {len(playlists)} ShotGrid playlists")
            else:
                print(f"ERROR: Failed to load playlists: {data.get('message')}")
                self._shotgrid_playlists = []
                self._shotgrid_playlists_data = []
                self.shotgridPlaylistsChanged.emit()

        except Exception as e:
            print(f"ERROR: Failed to load ShotGrid playlists: {e}")
            self._shotgrid_playlists = []
            self._shotgrid_playlists_data = []
            self.shotgridPlaylistsChanged.emit()

    @Slot(int)
    def selectShotgridPlaylist(self, index):
        """Select a ShotGrid playlist by index"""
        if (
            not hasattr(self, "_shotgrid_playlists_data")
            or index < 0
            or index >= len(self._shotgrid_playlists_data)
        ):
            print(f"ERROR: Invalid playlist index: {index}")
            return

        playlist = self._shotgrid_playlists_data[index]
        self._selected_playlist_id = playlist["id"]
        print(f"Selected ShotGrid playlist: {playlist['code']} (ID: {playlist['id']})")

    @Slot()
    def loadShotgridPlaylist(self):
        """Load versions from the selected ShotGrid playlist"""
        if not hasattr(self, "_selected_playlist_id") or not self._selected_playlist_id:
            print("ERROR: No playlist selected")
            return

        playlist_id = self._selected_playlist_id
        print(f"Loading versions from ShotGrid playlist ID: {playlist_id}")

        try:
            response = self._make_request(
                "GET", f"/shotgrid/playlist-items/{playlist_id}"
            )
            data = response.json()

            if data.get("status") == "success":
                items = data.get("items", [])
                print(f"✓ Loaded {len(items)} items from ShotGrid playlist")

                # Create versions via backend API
                for item in items:
                    # Item format is "shot_name/version_name"
                    try:
                        # Create version via backend
                        create_response = self._make_request(
                            "POST",
                            "/versions",
                            json={"name": item, "user_notes": "", "ai_notes": ""},
                        )

                        if create_response.status_code == 200:
                            print(f"  ✓ Created version: {item}")
                        else:
                            print(
                                f"  ✗ Failed to create version: {item} - {create_response.text}"
                            )

                    except Exception as e:
                        print(f"  ✗ Error creating version {item}: {e}")

                # Emit signal to reload versions
                self.versionsLoaded.emit()

            else:
                print(f"ERROR: Failed to load playlist items: {data.get('message')}")

        except Exception as e:
            print(f"ERROR: Failed to load ShotGrid playlist: {e}")
