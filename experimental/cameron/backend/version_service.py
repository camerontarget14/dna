"""
Version Service - Manages versions and their associated notes
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import csv
from io import StringIO

router = APIRouter()


# ===== Data Models =====


class Version(BaseModel):
    """A version with its associated data"""

    id: str
    name: str  # Display name (from leftmost CSV column)
    user_notes: str = ""
    ai_notes: str = ""
    transcript: str = ""


class AddNoteRequest(BaseModel):
    """Request to add a note to a version"""

    version_id: str
    note_text: str


class UpdateNotesRequest(BaseModel):
    """Request to update all notes for a version"""

    version_id: str
    user_notes: Optional[str] = None
    ai_notes: Optional[str] = None
    transcript: Optional[str] = None


class GenerateAINotesRequest(BaseModel):
    """Request to generate AI notes from transcript"""

    version_id: str
    transcript: Optional[str] = (
        None  # If not provided, uses version's existing transcript
    )


# ===== In-Memory Storage =====
# In production, this would be replaced with a database
_versions: Dict[str, Version] = {}
_version_order: List[str] = []  # To maintain insertion order


# ===== API Endpoints =====


@router.post("/versions/upload-csv")
async def upload_csv(file: UploadFile = File(...)):
    """
    Upload a CSV file to create versions.
    CSV format:
    - First column: Version Name (required)
    - Optional "ID" column: Version ID
    - Header row is skipped
    """
    content = await file.read()
    decoded = content.decode("utf-8", errors="ignore")
    reader = csv.reader(StringIO(decoded))

    # Read header row
    header = next(reader, None)
    if not header:
        raise HTTPException(status_code=400, detail="CSV file is empty")

    # Version Name is ALWAYS the first column (leftmost)
    version_name_idx = 0

    # Look for "ID" column for Version ID (optional)
    version_id_idx = None
    for idx, col in enumerate(header):
        col_lower = col.lower().strip()
        if col_lower == "id":
            version_id_idx = idx
            break

    # Read data rows (header is already skipped)
    versions_data = []
    for row in reader:
        if row and len(row) > 0 and row[0].strip():  # Skip empty rows
            version_name = row[0].strip()

            # Get ID from ID column if present, otherwise use name as ID
            if (
                version_id_idx is not None
                and len(row) > version_id_idx
                and row[version_id_idx].strip()
            ):
                version_id = row[version_id_idx].strip()
            else:
                version_id = version_name

            versions_data.append({"id": version_id, "name": version_name})

    # Clear existing versions and add new ones
    _versions.clear()
    _version_order.clear()

    for version_data in versions_data:
        version = Version(
            id=version_data["id"],
            name=version_data["name"],
            user_notes="",
            ai_notes="",
            transcript="",
        )
        _versions[version.id] = version
        _version_order.append(version.id)

    print(
        f"Loaded {len(_versions)} versions from CSV (ID column {'found' if version_id_idx is not None else 'not found'})"
    )

    return {
        "status": "success",
        "count": len(_versions),
        "versions": [{"id": v.id, "name": v.name} for v in _versions.values()],
    }


@router.post("/versions")
async def create_version(version: Version):
    """Create a new version"""
    # Check if version already exists
    if version.id in _versions:
        print(f"Version '{version.id}' already exists, updating...")
        _versions[version.id] = version
    else:
        print(f"Creating new version: {version.name} (ID: {version.id})")
        _versions[version.id] = version
        _version_order.append(version.id)

    return {"status": "success", "version": version.model_dump()}


@router.get("/versions")
async def get_versions():
    """Get all versions in order"""
    return {
        "status": "success",
        "count": len(_versions),
        "versions": [_versions[vid].model_dump() for vid in _version_order],
    }


@router.get("/versions/{version_id}")
async def get_version(version_id: str):
    """Get a specific version by ID"""
    if version_id not in _versions:
        raise HTTPException(status_code=404, detail=f"Version '{version_id}' not found")

    return {"status": "success", "version": _versions[version_id].model_dump()}


@router.post("/versions/{version_id}/notes")
async def add_note(version_id: str, request: AddNoteRequest):
    """Add a user note to a version"""
    if version_id not in _versions:
        raise HTTPException(status_code=404, detail=f"Version '{version_id}' not found")

    version = _versions[version_id]

    # Format note with "User:" prefix
    formatted_note = f"User: {request.note_text.strip()}"

    # Append to existing notes
    if version.user_notes:
        version.user_notes += "\n\n" + formatted_note
    else:
        version.user_notes = formatted_note

    print(f"Added note to version '{version.name}': {formatted_note}")

    return {"status": "success", "version": version.model_dump()}


@router.put("/versions/{version_id}/notes")
async def update_notes(version_id: str, request: UpdateNotesRequest):
    """Update notes for a version"""
    if version_id not in _versions:
        raise HTTPException(status_code=404, detail=f"Version '{version_id}' not found")

    version = _versions[version_id]

    if request.user_notes is not None:
        version.user_notes = request.user_notes
    if request.ai_notes is not None:
        version.ai_notes = request.ai_notes
    if request.transcript is not None:
        version.transcript = request.transcript

    return {"status": "success", "version": version.model_dump()}


@router.post("/versions/{version_id}/generate-ai-notes")
async def generate_ai_notes(version_id: str, request: GenerateAINotesRequest):
    """Generate AI notes from transcript for a version"""
    if version_id not in _versions:
        raise HTTPException(status_code=404, detail=f"Version '{version_id}' not found")

    version = _versions[version_id]

    # Use provided transcript or version's existing transcript
    transcript = request.transcript if request.transcript else version.transcript

    if not transcript:
        raise HTTPException(
            status_code=400, detail="No transcript available for AI note generation"
        )

    # Import the LLM summary function from note_service
    from note_service import LLMSummaryRequest
    import httpx

    # Call the LLM summary endpoint (internal call)
    # In a real implementation, you might want to import and call the function directly
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/llm-summary", json={"text": transcript}
        )

        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to generate AI notes")

        result = response.json()
        ai_notes = result.get("summary", "")

    # Store AI notes in version
    version.ai_notes = ai_notes

    return {"status": "success", "version": version.model_dump()}


@router.delete("/versions/{version_id}")
async def delete_version(version_id: str):
    """Delete a version"""
    if version_id not in _versions:
        raise HTTPException(status_code=404, detail=f"Version '{version_id}' not found")

    del _versions[version_id]
    _version_order.remove(version_id)

    return {"status": "success", "message": f"Version '{version_id}' deleted"}


@router.delete("/versions")
async def clear_versions():
    """Clear all versions"""
    count = len(_versions)
    _versions.clear()
    _version_order.clear()

    return {"status": "success", "message": f"Cleared {count} versions"}


@router.get("/versions/export/csv")
async def export_csv():
    """Export all versions and their notes to CSV format"""
    from fastapi.responses import StreamingResponse
    from io import StringIO

    output = StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(["Version", "Note", "Transcript"])

    # Write each version's notes
    for version_id in _version_order:
        version = _versions[version_id]

        # Split notes by double newline (each note from a user)
        notes = version.user_notes.split("\n\n") if version.user_notes else []

        if notes:
            # Write each note as a separate row
            for note in notes:
                if note.strip():
                    writer.writerow([version.name, note.strip(), version.transcript])
        else:
            # Write version even if no notes (with empty note field)
            writer.writerow([version.name, "", version.transcript])

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=versions_export.csv"},
    )
