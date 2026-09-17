from typing import Any

from fastapi import APIRouter, UploadFile, File, HTTPException

from services.document_service import (
    extract_document_text,
    DocumentProcessingError,
    DocumentResult,
)


router = APIRouter(
    prefix="/api/v1/analysis",
    tags=["Document Analysis"],
)


@router.post("/document")
async def analyze_document(
    file: UploadFile = File(...)
) -> dict[str, Any]:

    try:
        filename = file.filename

        if not filename:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file must have a filename.",
            )

        content = await file.read()

        result: DocumentResult = extract_document_text(
            filename=filename,
            content=content,
        )

        return {
            "success": True,
            "message": "Document processed successfully.",
            "document": result,
        }

    except DocumentProcessingError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    finally:
        await file.close()