from typing import Any

from fastapi import (
    APIRouter,
    HTTPException,
)
from pydantic import BaseModel, Field

from services.draft_service import (
    DraftServiceError,
    get_draft_type,
    validate_draft_details,
)
from services.draft_legal_service import (
    DraftLegalServiceError,
    retrieve_draft_legal_requirements,
)
from services.draft_ai_service import (
    DraftAIServiceError,
    generate_draft,
)
from services.draft_validation_service import (
    DraftValidationError,
    validate_generated_draft,
)


router = APIRouter(
    prefix="/api/v1/draft",
    tags=["Draft"],
)


class DraftCreateRequest(BaseModel):
    draft_type: str = Field(
        ...,
        min_length=1,
    )

    details: dict[str, Any] = Field(
        default_factory=dict,
    )


@router.post("/create")
async def create_draft(
    request: DraftCreateRequest,
) -> dict[str, Any]:

    try:
        draft_type = (
            request.draft_type
            .strip()
            .lower()
        )

        draft_config = get_draft_type(
            draft_type
        )

        details = validate_draft_details(
            draft_type=draft_type,
            details=request.details,
        )

        legal_requirements = (
            retrieve_draft_legal_requirements(
                draft_type=draft_type,
                limit_per_query=3,
            )
        )

        ai_result = generate_draft(
            draft_type=draft_type,
            details=details,
            legal_requirements=(
                legal_requirements
            ),
        )

        validated_result = (
            validate_generated_draft(
                ai_result=ai_result,
                legal_requirements=(
                    legal_requirements
                ),
            )
        )

        return {
            "success": True,
            "message": (
                "Draft created successfully."
            ),
            "draft_type": draft_type,
            "draft_type_name": (
                draft_config["name"]
            ),
            "legal_requirements_retrieved": (
                len(legal_requirements)
            ),
            "result": validated_result,
        }

    except DraftServiceError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except DraftLegalServiceError as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc

    except DraftAIServiceError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc

    except DraftValidationError as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Draft creation failed: "
                f"{str(exc)}"
            ),
        ) from exc