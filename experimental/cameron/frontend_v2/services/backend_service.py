"""
Backend API Service
Handles communication with the FastAPI backend server
"""

import requests
from PySide6.QtCore import QObject, Signal, Property, Slot


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

    # LLM API Keys and Prompts
    openaiApiKeyChanged = Signal()
    openaiPromptChanged = Signal()
    claudeApiKeyChanged = Signal()
    claudePromptChanged = Signal()
    llamaApiKeyChanged = Signal()
    llamaPromptChanged = Signal()

    # ShotGrid
    shotgridProjectsChanged = Signal()
    shotgridPlaylistsChanged = Signal()

    def __init__(self, backend_url="http://localhost:8000"):
        super().__init__()
        self._backend_url = backend_url

        # User info
        self._user_name = ""
        self._meeting_id = ""

        # Current version
        self._selected_version_id = None
        self._selected_version_name = ""

        # Notes and transcript
        self._current_notes = ""
        self._current_ai_notes = ""
        self._current_transcript = ""
        self._staging_note = ""

        # LLM API Keys and Prompts
        self._openai_api_key = ""
        self._openai_prompt = (
            "Summarize the following transcript and provide key notes:"
        )
        self._claude_api_key = ""
        self._claude_prompt = (
            "Summarize the following transcript and provide key notes:"
        )
        self._llama_api_key = ""
        self._llama_prompt = "Summarize the following transcript and provide key notes:"

        # ShotGrid
        self._shotgrid_projects = []
        self._shotgrid_playlists = []
        self._selected_project_id = None
        self._selected_playlist_id = None

    # User Name
    @Property(str, notify=userNameChanged)
    def userName(self):
        return self._user_name

    @userName.setter
    def userName(self, value):
        if self._user_name != value:
            self._user_name = value
            self.userNameChanged.emit()

    # Meeting ID
    @Property(str, notify=meetingIdChanged)
    def meetingId(self):
        return self._meeting_id

    @meetingId.setter
    def meetingId(self, value):
        if self._meeting_id != value:
            self._meeting_id = value
            self.meetingIdChanged.emit()

    # Selected Version
    @Property(str, notify=selectedVersionIdChanged)
    def selectedVersionId(self):
        return self._selected_version_id or ""

    @Property(str, notify=selectedVersionNameChanged)
    def selectedVersionName(self):
        return self._selected_version_name

    # Notes and Transcript
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

    # OpenAI
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

    # Claude
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

    # Llama
    @Property(str, notify=llamaApiKeyChanged)
    def llamaApiKey(self):
        return self._llama_api_key

    @llamaApiKey.setter
    def llamaApiKey(self, value):
        if self._llama_api_key != value:
            self._llama_api_key = value
            self.llamaApiKeyChanged.emit()

    @Property(str, notify=llamaPromptChanged)
    def llamaPrompt(self):
        return self._llama_prompt

    @llamaPrompt.setter
    def llamaPrompt(self, value):
        if self._llama_prompt != value:
            self._llama_prompt = value
            self.llamaPromptChanged.emit()

    # ShotGrid
    @Property("QStringList", notify=shotgridProjectsChanged)
    def shotgridProjects(self):
        return self._shotgrid_projects

    @Property("QStringList", notify=shotgridPlaylistsChanged)
    def shotgridPlaylists(self):
        return self._shotgrid_playlists

    # API Methods
    def fetch_versions(self):
        """Fetch versions from backend"""
        try:
            # For now, return test data
            # In production, this would call: requests.get(f"{self._backend_url}/versions")
            return [
                {"id": "1", "description": "Version 4336737"},
                {"id": "2", "description": "HSM_SATL_0020_TD_v003"},
                {"id": "3", "description": "HSM_SATL_0020_ANIM_v003"},
            ]
        except Exception as e:
            print(f"Error fetching versions: {e}")
            return []

    @Slot(str)
    def selectVersion(self, version_id):
        """Select a version"""
        self._selected_version_id = version_id
        self.selectedVersionIdChanged.emit()

        # Fetch version details
        # In production: requests.get(f"{self._backend_url}/versions/{version_id}")
        self._selected_version_name = f"Version {version_id}"
        self.selectedVersionNameChanged.emit()

        # Load notes, transcript, etc.
        self._current_notes = ""
        self.currentNotesChanged.emit()

        self._current_transcript = ""
        self.currentTranscriptChanged.emit()

    @Slot()
    def sendNote(self):
        """Send the staged note"""
        if not self._staging_note.strip() or not self._selected_version_id:
            return

        # Format note with user name
        formatted_note = f"{self._user_name}: {self._staging_note.strip()}"

        # Add to current notes
        separator = "\n\n" if self._current_notes else ""
        self._current_notes += separator + formatted_note
        self.currentNotesChanged.emit()

        # Clear staging
        self._staging_note = ""
        self.stagingNoteChanged.emit()

        # In production: POST to backend API
        # requests.post(f"{self._backend_url}/versions/{self._selected_version_id}/notes",
        #               json={"note": formatted_note})

    @Slot()
    def generateNotes(self):
        """Generate AI notes"""
        # Check if any API key is set
        has_api_key = bool(
            self._openai_api_key or self._claude_api_key or self._llama_api_key
        )

        if not has_api_key:
            self._current_ai_notes = "Test Output: Please add an API Key"
        else:
            # For now, show which provider would be used
            if self._openai_api_key:
                self._current_ai_notes = "Test Output: Would use OpenAI API"
            elif self._claude_api_key:
                self._current_ai_notes = "Test Output: Would use Claude API"
            elif self._llama_api_key:
                self._current_ai_notes = "Test Output: Would use Llama API"

        self.currentAiNotesChanged.emit()

        # In production: POST to backend to generate notes
        # requests.post(f"{self._backend_url}/versions/{self._selected_version_id}/generate-notes")

    @Slot()
    def addAiNotesToStaging(self):
        """Add AI notes to staging area"""
        if not self._current_ai_notes:
            return

        separator = "\n\n" if self._staging_note else ""
        self._staging_note += separator + self._current_ai_notes
        self.stagingNoteChanged.emit()

    @Slot()
    def joinMeeting(self):
        """Join meeting (connect to Vexa WebSocket)"""
        print("Join Meeting clicked - WebSocket connection will be implemented")
        # In production: Connect to Vexa WebSocket service
        # This will be implemented in Phase 3

    @Slot(int)
    def selectShotgridProject(self, index):
        """Select a ShotGrid project"""
        if index < 0 or index >= len(self._shotgrid_projects):
            return

        print(f"Selected ShotGrid project: {self._shotgrid_projects[index]}")
        # In production: Load playlists for this project
        self._shotgrid_playlists = ["Playlist 1", "Playlist 2", "Playlist 3"]
        self.shotgridPlaylistsChanged.emit()

    @Slot(int)
    def selectShotgridPlaylist(self, index):
        """Select a ShotGrid playlist"""
        if index < 0 or index >= len(self._shotgrid_playlists):
            return

        print(f"Selected ShotGrid playlist: {self._shotgrid_playlists[index]}")
        # In production: Load versions from this playlist

    @Slot(str)
    def importCSV(self, file_url):
        """Import versions from CSV file"""
        # Convert QML URL to file path
        file_path = file_url.toString().replace("file://", "")
        print(f"Import CSV: {file_path}")

        # In production: Parse CSV and load versions
        # This will be implemented in Phase 2

    @Slot(str)
    def exportCSV(self, file_url):
        """Export notes to CSV file"""
        # Convert QML URL to file path
        file_path = file_url.toString().replace("file://", "")
        print(f"Export CSV: {file_path}")

        # In production: Format notes as CSV and save
        # Format: Version, Note, Transcript
        # Each note gets its own row (split by \n\n)
        # This will be implemented in Phase 2
