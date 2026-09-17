from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, UploadFile

from core.config import settings
from schemas.upload import UploadResponse

router = APIRouter()


@router.post("", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)) -> UploadResponse:
    """Basic upload endpoint. Agentic processing will be added later."""
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    original_name = file.filename or "uploaded_file"
    suffix = Path(original_name).suffix
    stored_name = f"{uuid4().hex}{suffix}"
    destination = upload_dir / stored_name

    content = await file.read()
    destination.write_bytes(content)

    return UploadResponse(
        filename=original_name,
        stored_name=stored_name,
        size=len(content),
        message="File uploaded successfully. AI processing is not connected yet.",
    )
