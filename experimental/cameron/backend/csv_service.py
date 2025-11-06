"""
CSV Service - Handles CSV import and export operations
"""

import csv
from io import StringIO

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

router = APIRouter()


@router.post("/upload-playlist")
async def upload_playlist(file: UploadFile = File(...)):
    """
    Upload a CSV file to extract playlist items.
    Returns the first column of each row (excluding header).
    """
    content = await file.read()
    decoded = content.decode("utf-8", errors="ignore").splitlines()
    reader = csv.reader(decoded)
    items = []
    print("CSV file contents:")
    for idx, row in enumerate(reader):
        if not row:
            continue
        print(row)
        if idx == 0:  # skip header row
            continue
        first = row[0].strip()
        if first:
            items.append(first)
    return {"status": "success", "items": items}


@router.post("/versions/upload-csv")
async def upload_versions_csv(file: UploadFile = File(...)):
    """
    Upload a CSV file to create versions.
    CSV format:
    - First column: Version Name (required)
    - Optional "ID" column: Version ID
    - Header row is skipped
    """
    # Import here to avoid circular dependency
    from version_service import Version, _version_order, _versions

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


@router.get("/versions/export/csv")
async def export_versions_csv():
    """Export all versions and their notes to CSV format"""
    # Import here to avoid circular dependency
    from version_service import _version_order, _versions

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
