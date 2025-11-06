"""
Version Service - Manages versions and their associated notes
"""

from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

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


# ===== In-Memory Storage =====
# In production, this would be replaced with a database
_versions: Dict[str, Version] = {}
_version_order: List[str] = []  # To maintain insertion order


# ===== API Endpoints =====


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
