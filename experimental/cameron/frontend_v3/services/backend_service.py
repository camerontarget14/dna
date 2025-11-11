"""
Backend API Service
Handles communication with the FastAPI backend server
ONLY uses backend API - no local storage
"""

import requests
from config import BACKEND_URL, CONNECTION_RETRY_ATTEMPTS, DEBUG_MODE, REQUEST_TIMEOUT
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
    shotgridUrlChanged = Signal()
    shotgridApiKeyChanged = Signal()
    shotgridScriptNameChanged = Signal()
    includeStatusesChanged = Signal()
    versionStatusesChanged = Signal()
    selectedVersionStatusChanged = Signal()

    # Versions
    versionsLoaded = Signal()

    # Vexa/Meeting signals
    meetingStatusChanged = Signal()
    vexaApiKeyChanged = Signal()
    vexaApiUrlChanged = Signal()

    def __init__(self, backend_url=None):
        super().__init__()
        # Use provided URL, environment variable, or default
        self._backend_url = backend_url or BACKEND_URL
        self._request_timeout = REQUEST_TIMEOUT
        self._retry_attempts = CONNECTION_RETRY_ATTEMPTS

        if DEBUG_MODE:
            print(f"[DEBUG] Backend URL: {self._backend_url}")
            print(f"[DEBUG] Request timeout: {self._request_timeout}s")
            print(f"[DEBUG] Retry attempts: {self._retry_attempts}")

        self._check_backend_connection()

        # User info
        self._user_name = ""
        self._meeting_id = ""

        # Vexa integration
        self._vexa_api_key = ""
        self._vexa_api_url = "https://api.cloud.vexa.ai"
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
        self._claude_api_key = ""
        self._gemini_api_key = ""

        # Default LLM prompt (short mode from llm_prompts.factory.yaml)
        default_prompt = """You are a helpful assistant that reviews transcripts of artist review meetings and generates concise, readable summaries of the discussions.

The meetings are focused on reviewing creative work submissions ("shots") for a movie. Each meeting involves artists and reviewers (supervisors, leads, etc.) discussing feedback, decisions, and next steps for each shot.

Your goal is to recreate short, clear, and accurate abbreviated conversations that capture:
- Key feedback points
- Decisions made (e.g., approved/finalled shots)
- Any actionable tasks for the artist

Write in a concise, natural tone that's easy for artists to quickly scan and understand what was said and what they need to do next."""

        self._openai_prompt = default_prompt
        self._claude_prompt = default_prompt
        self._gemini_prompt = default_prompt

        # ShotGrid
        self._shotgrid_projects = []
        self._shotgrid_playlists = []
        self._shotgrid_projects_data = []
        self._shotgrid_playlists_data = []
        self._selected_project_id = None
        self._selected_playlist_id = None
        self._shotgrid_url = ""
        self._shotgrid_api_key = ""
        self._shotgrid_script_name = ""
        self._include_statuses = False
        self._version_statuses = []  # List of display names for UI
        self._version_status_codes = {}  # Dict mapping display names to codes
        self._selected_version_status = ""

        # Per-version notes storage (version_id -> note_text)
        self._version_notes = {}
        self._current_version_note = ""

        # Transcript segment tracking for version-specific routing
        self._version_activation_time = (
            None  # Timestamp when current version was activated
        )
        self._seen_segment_ids = (
            set()
        )  # Track which segment IDs we've already processed for this version

        # Load settings from .env file
        self.load_settings()

        # Check if ShotGrid is enabled and load projects
        self._check_shotgrid_enabled()

        # Create a default scratch version for notes
        self._create_scratch_version()

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

    def _create_scratch_version(self):
        """Create a default scratch version that's always available"""
        try:
            scratch_version = {
                "id": "_scratch",
                "name": "Scratch Notes",
                "user_notes": "",
                "ai_notes": "",
                "transcript": "",
                "status": "",
            }
            response = self._make_request("POST", "/versions", json=scratch_version)
            if response.status_code == 200:
                self._selected_version_id = "_scratch"
                self._version_notes["_scratch"] = ""
                self._current_version_note = ""
                self.selectedVersionIdChanged.emit()
                self.selectedVersionNameChanged.emit()
                print("✓ Created default scratch version")
        except Exception as e:
            print(f"Warning: Could not create scratch version: {e}")

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
        """Make a request to the backend API with error handling and retries"""
        url = f"{self._backend_url}{endpoint}"

        # Set timeout if not provided
        if "timeout" not in kwargs:
            kwargs["timeout"] = self._request_timeout

        # Retry logic
        last_exception = None
        for attempt in range(self._retry_attempts):
            try:
                if DEBUG_MODE and attempt > 0:
                    print(f"[DEBUG] Retry attempt {attempt + 1}/{self._retry_attempts}")

                response = requests.request(method, url, **kwargs)
                response.raise_for_status()
                return response

            except requests.exceptions.RequestException as e:
                last_exception = e
                if attempt < self._retry_attempts - 1:
                    # Don't print on last attempt (will be handled below)
                    if DEBUG_MODE:
                        print(f"[DEBUG] Request failed (attempt {attempt + 1}): {e}")
                    continue

        # All retries failed
        print(
            f"ERROR: API request failed after {self._retry_attempts} attempts: {method} {endpoint}"
        )
        print(f"  Error: {last_exception}")
        raise last_exception

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
            self.save_setting("openai_api_key", value)

    @Property(str, notify=openaiPromptChanged)
    def openaiPrompt(self):
        return self._openai_prompt

    @openaiPrompt.setter
    def openaiPrompt(self, value):
        if self._openai_prompt != value:
            self._openai_prompt = value
            self.openaiPromptChanged.emit()
            self.save_setting("openai_prompt", value)

    @Property(str, notify=claudeApiKeyChanged)
    def claudeApiKey(self):
        return self._claude_api_key

    @claudeApiKey.setter
    def claudeApiKey(self, value):
        if self._claude_api_key != value:
            self._claude_api_key = value
            self.claudeApiKeyChanged.emit()
            self.save_setting("claude_api_key", value)

    @Property(str, notify=claudePromptChanged)
    def claudePrompt(self):
        return self._claude_prompt

    @claudePrompt.setter
    def claudePrompt(self, value):
        if self._claude_prompt != value:
            self._claude_prompt = value
            self.claudePromptChanged.emit()
            self.save_setting("claude_prompt", value)

    @Property(str, notify=geminiApiKeyChanged)
    def geminiApiKey(self):
        return self._gemini_api_key

    @geminiApiKey.setter
    def geminiApiKey(self, value):
        if self._gemini_api_key != value:
            self._gemini_api_key = value
            self.geminiApiKeyChanged.emit()
            self.save_setting("gemini_api_key", value)

    @Property(str, notify=geminiPromptChanged)
    def geminiPrompt(self):
        return self._gemini_prompt

    @geminiPrompt.setter
    def geminiPrompt(self, value):
        if self._gemini_prompt != value:
            self._gemini_prompt = value
            self.geminiPromptChanged.emit()
            self.save_setting("gemini_prompt", value)

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

            # Load status (convert code to display name for UI)
            status_code = version.get("status", "")
            # Find the display name for this code
            self._selected_version_status = ""
            for display_name, code in self._version_status_codes.items():
                if code == status_code:
                    self._selected_version_status = display_name
                    break

            # Load per-version note
            self._current_version_note = self._version_notes.get(version_id, "")

            # Clear staging
            self._staging_note = ""

            # Reset transcript tracking for new version - start fresh
            import time

            self._version_activation_time = time.time()
            self._seen_segment_ids = set()  # Clear the set of seen segments

            # Mark all CURRENT segments in the meeting as "seen" (async, non-blocking)
            # so we only capture NEW segments that arrive after this point
            # Using QTimer to make it async and not block the UI
            QTimer.singleShot(0, self._mark_current_segments_as_seen)

            print(
                f"  Reset transcript tracking - will only capture new segments from now on"
            )

            # Emit signals
            self.selectedVersionIdChanged.emit()
            self.selectedVersionNameChanged.emit()
            self.currentNotesChanged.emit()
            self.currentAiNotesChanged.emit()
            self.currentTranscriptChanged.emit()
            self.currentVersionNoteChanged.emit()
            self.stagingNoteChanged.emit()
            self.selectedVersionStatusChanged.emit()

            print(f"✓ Loaded version '{self._selected_version_name}'")
            print(f"  User notes: {len(self._current_notes)} chars")
            print(f"  AI notes: {len(self._current_ai_notes)} chars")
            print(f"  Version note: {len(self._current_version_note)} chars")
            print(f"  Transcript: {len(self._current_transcript)} chars")

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

        # Determine which provider, prompt, and API key to use based on API keys
        provider = None
        prompt = None
        api_key = None

        if self._openai_api_key:
            provider = "openai"
            prompt = self._openai_prompt
            api_key = self._openai_api_key
        elif self._gemini_api_key:
            provider = "gemini"
            prompt = self._gemini_prompt
            api_key = self._gemini_api_key
        elif self._claude_api_key:
            provider = "claude"
            prompt = self._claude_prompt
            api_key = self._claude_api_key

        print(f"Generating AI notes for version '{self._selected_version_name}'...")
        if provider:
            print(f"  Using provider: {provider}")

        try:
            response = self._make_request(
                "POST",
                f"/versions/{self._selected_version_id}/generate-ai-notes",
                json={
                    "version_id": self._selected_version_id,
                    "transcript": self._current_transcript,
                    "prompt": prompt,
                    "provider": provider,
                    "api_key": api_key,
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

        # Sync to backend
        try:
            response = self._make_request(
                "GET", f"/versions/{self._selected_version_id}"
            )
            if response.status_code == 200:
                version_data = response.json().get("version", {})
                version_data["user_notes"] = note_text
                self._make_request("POST", "/versions", json=version_data)
        except Exception as e:
            print(f"ERROR: Failed to sync note to backend: {e}")

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
            self.save_setting("vexa_api_key", value)
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
            self.save_setting("vexa_api_url", value)
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
                self._meeting_id, language="auto", bot_name="Dailies Notes Assistant"
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
        self._transcription_timer.start(
            1000
        )  # Poll every 1 second for real-time updates

        print("Started transcription polling (every 1 second)")

        # Do initial fetch
        self._poll_transcription()

    def _stop_transcription_polling(self):
        """Stop polling for transcription updates"""
        if self._transcription_timer:
            self._transcription_timer.stop()
            self._transcription_timer = None
            print("Stopped transcription polling")

    def _mark_current_segments_as_seen(self):
        """Mark all current meeting segments as seen (called when switching versions)"""
        if not self._current_meeting_id or not self._vexa_service:
            return

        try:
            transcription_data = self._vexa_service.get_transcription(
                self._current_meeting_id
            )

            segments = transcription_data.segments
            if segments:
                # Mark all existing segment IDs as seen
                for seg in segments:
                    segment_id = seg.get("id") or seg.get("timestamp", "")
                    if segment_id:
                        self._seen_segment_ids.add(segment_id)

                print(f"  Marked {len(segments)} existing segments as seen")

        except Exception as e:
            # Not critical if this fails
            pass

    def _poll_transcription(self):
        """Poll for transcription updates and route to active version"""
        if not self._current_meeting_id or not self._vexa_service:
            return

        # Only route transcripts if a version is selected
        if not self._selected_version_id or self._version_activation_time is None:
            return

        try:
            transcription_data = self._vexa_service.get_transcription(
                self._current_meeting_id
            )

            # Get all segments from the meeting
            segments = transcription_data.segments
            if not segments:
                return

            # Filter to only NEW segments we haven't seen yet (by segment ID)
            new_segments = []
            for seg in segments:
                segment_id = seg.get("id") or seg.get("timestamp", "")
                # Only process segments we haven't seen before
                if segment_id and segment_id not in self._seen_segment_ids:
                    new_segments.append(seg)
                    self._seen_segment_ids.add(segment_id)  # Mark as seen

            if new_segments:
                # Append only NEW segments to the current version's transcript
                new_text = "\n".join(
                    [
                        f"{seg.get('speaker', 'Unknown')}: {seg.get('text', '')}"
                        for seg in new_segments
                    ]
                )

                # Append to existing transcript (don't replace)
                if self._current_transcript:
                    self._current_transcript += "\n" + new_text
                else:
                    self._current_transcript = new_text

                self.currentTranscriptChanged.emit()

                # Save the updated transcript to the currently active version in backend
                self._save_transcript_to_active_version(self._current_transcript)

                print(
                    f"Transcript updated for version '{self._selected_version_name}': +{len(new_segments)} new segments"
                )

        except Exception as e:
            # Don't spam errors, transcription might not be ready yet
            pass

    def _save_transcript_to_active_version(self, transcript_text):
        """Save transcript to the currently active version"""
        if not self._selected_version_id:
            return

        try:
            # Update the version's transcript in the backend
            response = self._make_request(
                "PUT",
                f"/versions/{self._selected_version_id}/notes",
                json={
                    "version_id": self._selected_version_id,
                    "transcript": transcript_text,
                },
            )

            if response.status_code == 200:
                print(
                    f"  ✓ Saved transcript to version '{self._selected_version_name}'"
                )
            else:
                print(f"  ✗ Failed to save transcript: {response.text}")

        except Exception as e:
            print(f"  ✗ Error saving transcript: {e}")

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
            # Pass includeStatuses parameter if status mode is enabled
            params = {"include_status": self._include_statuses}
            response = self._make_request("GET", "/versions/export/csv", params=params)

            # Write response content to file
            with open(file_path, "wb") as f:
                f.write(response.content)

            status_info = " (with Status column)" if self._include_statuses else ""
            print(f"✓ Exported versions to CSV{status_info}: {file_path}")

        except Exception as e:
            print(f"ERROR: Failed to export CSV: {e}")

    # ===== ShotGrid Integration =====

    @Property(list, notify=shotgridProjectsChanged)
    def shotgridProjects(self):
        return self._shotgrid_projects

    @Property(list, notify=shotgridPlaylistsChanged)
    def shotgridPlaylists(self):
        return self._shotgrid_playlists

    @Property(str, notify=shotgridUrlChanged)
    def shotgridUrl(self):
        return self._shotgrid_url

    @shotgridUrl.setter
    def shotgridUrl(self, value):
        if self._shotgrid_url != value:
            self._shotgrid_url = value
            self.shotgridUrlChanged.emit()
            print(f"ShotGrid URL updated: {value}")
            self.save_setting("shotgrid_url", value)
            self._try_update_shotgrid_config()

    @Property(str, notify=shotgridApiKeyChanged)
    def shotgridApiKey(self):
        return self._shotgrid_api_key

    @shotgridApiKey.setter
    def shotgridApiKey(self, value):
        if self._shotgrid_api_key != value:
            self._shotgrid_api_key = value
            self.shotgridApiKeyChanged.emit()
            print("ShotGrid API Key updated")
            self.save_setting("shotgrid_api_key", value)
            self._try_update_shotgrid_config()

    @Property(str, notify=shotgridScriptNameChanged)
    def shotgridScriptName(self):
        return self._shotgrid_script_name

    @shotgridScriptName.setter
    def shotgridScriptName(self, value):
        if self._shotgrid_script_name != value:
            self._shotgrid_script_name = value
            self.shotgridScriptNameChanged.emit()
            print(f"ShotGrid Script Name updated: {value}")
            self.save_setting("shotgrid_script_name", value)
            self._try_update_shotgrid_config()

    @Property(bool, notify=includeStatusesChanged)
    def includeStatuses(self):
        return self._include_statuses

    @includeStatuses.setter
    def includeStatuses(self, value):
        if self._include_statuses != value:
            self._include_statuses = value
            self.includeStatusesChanged.emit()
            print(f"Include Statuses updated: {value}")
            self.save_setting("include_statuses", value)
            if value:
                self.loadVersionStatuses()

    @Property(list, notify=versionStatusesChanged)
    def versionStatuses(self):
        return self._version_statuses

    @Property(str, notify=selectedVersionStatusChanged)
    def selectedVersionStatus(self):
        # Return display name for UI
        return self._selected_version_status

    @selectedVersionStatus.setter
    def selectedVersionStatus(self, value):
        # value is the display name from UI
        if self._selected_version_status != value:
            self._selected_version_status = value
            self.selectedVersionStatusChanged.emit()
            print(f"Version status display name updated: {value}")
            # Convert display name to code before updating backend
            status_code = self._version_status_codes.get(value, value)
            print(f"  Status code: {status_code}")
            self.updateVersionStatus(status_code)

    def _try_update_shotgrid_config(self):
        """Auto-update backend config when all three values are set"""
        if self._shotgrid_url and self._shotgrid_api_key and self._shotgrid_script_name:
            self.updateShotGridConfig()

    @Slot()
    def updateShotGridConfig(self):
        """Send ShotGrid configuration to backend"""
        if (
            not self._shotgrid_url
            or not self._shotgrid_api_key
            or not self._shotgrid_script_name
        ):
            print("ERROR: ShotGrid configuration is incomplete")
            return

        try:
            payload = {
                "shotgrid_url": self._shotgrid_url,
                "script_name": self._shotgrid_script_name,
                "api_key": self._shotgrid_api_key,
            }

            response = self._make_request("POST", "/shotgrid/config", json=payload)
            data = response.json()

            if data.get("status") == "success":
                print("✓ ShotGrid configuration updated on backend")
                # Auto-load projects after configuration
                self.loadShotGridProjects()
            else:
                print(f"ERROR: Failed to update ShotGrid config: {data.get('message')}")

        except Exception as e:
            print(f"ERROR: Failed to update ShotGrid configuration: {e}")

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
        self._selected_project_id = project_id
        print(f"Selected ShotGrid project: {project['code']} (ID: {project_id})")

        # Load playlists for this project
        self.loadShotGridPlaylists(project_id)

        # Load version statuses for this project if includeStatuses is enabled
        if self._include_statuses:
            self.loadVersionStatuses()

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
                    # Extract just the version name (part after the /)
                    if "/" in item:
                        version_name = item.split("/")[-1]
                    else:
                        version_name = item

                    try:
                        # Create version via backend
                        create_response = self._make_request(
                            "POST",
                            "/versions",
                            json={
                                "id": version_name,
                                "name": version_name,
                                "user_notes": "",
                                "ai_notes": "",
                                "transcript": "",
                            },
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

                # If includeStatuses is enabled, load statuses for these versions
                if self._include_statuses:
                    self.loadPlaylistVersionsWithStatuses(playlist_id)

            else:
                print(f"ERROR: Failed to load playlist items: {data.get('message')}")

        except Exception as e:
            print(f"ERROR: Failed to load ShotGrid playlist: {e}")

    @Slot()
    def loadVersionStatuses(self):
        """Load available version statuses from ShotGrid for the selected project"""
        print("Loading version statuses from ShotGrid...")

        try:
            # Use project_id parameter if available to only get statuses used in that project
            params = {}
            if self._selected_project_id:
                params["project_id"] = self._selected_project_id
                print(
                    f"  Filtering statuses for project ID: {self._selected_project_id}"
                )

            response = self._make_request(
                "GET", "/shotgrid/version-statuses", params=params
            )
            data = response.json()

            if data.get("status") == "success":
                statuses_response = data.get("statuses", {})
                print(f"DEBUG: statuses_response type: {type(statuses_response)}")
                print(f"DEBUG: statuses_response content: {statuses_response}")

                # Handle both dict and list responses
                if isinstance(statuses_response, dict):
                    # status_dict is {code: display_name}
                    # We want to show display names in the UI but store codes in the backend
                    self._version_statuses = list(
                        statuses_response.values()
                    )  # Display names for UI
                    self._version_status_codes = {
                        v: k for k, v in statuses_response.items()
                    }  # Reverse map: name -> code
                elif isinstance(statuses_response, list):
                    # If it's a list of codes, use them as-is (no display names available)
                    self._version_statuses = statuses_response
                    self._version_status_codes = {
                        v: v for v in statuses_response
                    }  # Map code to itself
                else:
                    print(
                        f"ERROR: Unexpected statuses response type: {type(statuses_response)}"
                    )
                    self._version_statuses = []
                    self._version_status_codes = {}

                self.versionStatusesChanged.emit()
                print(f"✓ Loaded {len(self._version_statuses)} version statuses")
                print(f"  Display names: {self._version_statuses}")
                print(f"  Code mapping: {self._version_status_codes}")
            else:
                print(f"ERROR: Failed to load version statuses: {data.get('message')}")

        except Exception as e:
            print(f"ERROR: Failed to load version statuses: {e}")

    @Slot(int)
    def loadPlaylistVersionsWithStatuses(self, playlist_id):
        """Load versions with their statuses from a playlist"""
        print(f"Loading version statuses for playlist ID: {playlist_id}")

        try:
            response = self._make_request(
                "GET", f"/shotgrid/playlist-versions-with-statuses/{playlist_id}"
            )
            data = response.json()

            if data.get("status") == "success":
                versions = data.get("versions", [])
                print(f"✓ Loaded statuses for {len(versions)} versions")

                # Update each version's status via backend API
                for version_info in versions:
                    version_name = version_info.get("name", "")
                    status = version_info.get("status", "")

                    if version_name and status:
                        try:
                            # Extract just the version name (part after the /)
                            if "/" in version_name:
                                version_id = version_name.split("/")[-1]
                            else:
                                version_id = version_name

                            # Update version status via backend
                            update_response = self._make_request(
                                "PUT",
                                f"/versions/{version_id}/notes",
                                json={
                                    "version_id": version_id,
                                    "user_notes": None,
                                    "ai_notes": None,
                                    "transcript": None,
                                },
                            )

                            # Also update the version with status field
                            # We need to get the current version data first
                            get_response = self._make_request(
                                "GET", f"/versions/{version_id}"
                            )
                            if get_response.status_code == 200:
                                version_data = get_response.json().get("version", {})
                                version_data["status"] = status

                                # Update with new status
                                self._make_request(
                                    "POST", "/versions", json=version_data
                                )
                                print(
                                    f"  ✓ Updated status for {version_name}: {status}"
                                )

                        except Exception as e:
                            print(f"  ✗ Error updating status for {version_name}: {e}")

            else:
                print(f"ERROR: Failed to load version statuses: {data.get('message')}")

        except Exception as e:
            print(f"ERROR: Failed to load version statuses for playlist: {e}")

    @Slot(str)
    def updateVersionStatus(self, status):
        """Update the status of the currently selected version"""
        if not self._selected_version_id:
            print("ERROR: No version selected")
            return

        print(f"Updating status for version {self._selected_version_id} to: {status}")

        try:
            # Get current version data
            response = self._make_request(
                "GET", f"/versions/{self._selected_version_id}"
            )
            if response.status_code == 200:
                version_data = response.json().get("version", {})
                version_data["status"] = status

                # Update version with new status
                update_response = self._make_request(
                    "POST", "/versions", json=version_data
                )

                if update_response.status_code == 200:
                    print(f"✓ Updated version status to: {status}")
                else:
                    print(f"✗ Failed to update version status: {update_response.text}")

        except Exception as e:
            print(f"ERROR: Failed to update version status: {e}")

    # ===== Settings Persistence =====

    def load_settings(self):
        """Load settings from backend .env file"""
        try:
            response = self._make_request("GET", "/settings")
            data = response.json()

            if data.get("status") == "success":
                settings = data.get("settings", {})
                print(f"✓ Loaded settings from .env file")

                # Apply settings to properties
                if "shotgrid_url" in settings:
                    self._shotgrid_url = settings["shotgrid_url"]
                    self.shotgridUrlChanged.emit()

                if "shotgrid_api_key" in settings:
                    self._shotgrid_api_key = settings["shotgrid_api_key"]
                    self.shotgridApiKeyChanged.emit()

                if "shotgrid_script_name" in settings:
                    self._shotgrid_script_name = settings["shotgrid_script_name"]
                    self.shotgridScriptNameChanged.emit()

                if "vexa_api_key" in settings:
                    self._vexa_api_key = settings["vexa_api_key"]
                    self.vexaApiKeyChanged.emit()
                    if self._vexa_api_key:
                        self._vexa_service = VexaService(
                            self._vexa_api_key, self._vexa_api_url
                        )

                if "vexa_api_url" in settings:
                    self._vexa_api_url = settings["vexa_api_url"]
                    self.vexaApiUrlChanged.emit()

                if "openai_api_key" in settings:
                    self._openai_api_key = settings["openai_api_key"]
                    self.openaiApiKeyChanged.emit()

                if "claude_api_key" in settings:
                    self._claude_api_key = settings["claude_api_key"]
                    self.claudeApiKeyChanged.emit()

                if "gemini_api_key" in settings:
                    self._gemini_api_key = settings["gemini_api_key"]
                    self.geminiApiKeyChanged.emit()

                if "openai_prompt" in settings:
                    self._openai_prompt = settings["openai_prompt"]
                    self.openaiPromptChanged.emit()

                if "claude_prompt" in settings:
                    self._claude_prompt = settings["claude_prompt"]
                    self.claudePromptChanged.emit()

                if "gemini_prompt" in settings:
                    self._gemini_prompt = settings["gemini_prompt"]
                    self.geminiPromptChanged.emit()

                if "include_statuses" in settings:
                    self._include_statuses = settings["include_statuses"]
                    self.includeStatusesChanged.emit()

                return True
            else:
                print(
                    f"Failed to load settings: {data.get('message', 'Unknown error')}"
                )
                return False

        except Exception as e:
            print(f"ERROR: Failed to load settings: {e}")
            return False

    def save_setting(self, field_name: str, value):
        """Save a single setting to .env file"""
        try:
            response = self._make_request(
                "POST", "/settings/save-partial", json={field_name: value}
            )

            data = response.json()
            if data.get("status") == "success":
                print(f"✓ Saved setting: {field_name}")
                return True
            else:
                print(f"Failed to save setting: {data.get('message', 'Unknown error')}")
                return False

        except Exception as e:
            print(f"ERROR: Failed to save setting {field_name}: {e}")
            return False
