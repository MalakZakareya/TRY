from typing import Any, cast

from fastapi import (
    APIRouter,
    File,
    HTTPException,
    UploadFile,
)

from services.document_service import (
    DocumentProcessingError,
    DocumentResult,
    extract_document_text,
)

from services.ai_service import (
    analyze_document_text,
)

from services.legal_analysis_service import (
    compare_point_with_regulations,
    retrieve_laws_for_points,
)


router = APIRouter(
    prefix="/api/v1/analysis",
    tags=["Document Analysis"],
)


def get_valid_points(
    ai_analysis: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Safely extract document points
    returned by the AI.
    """

    raw_points: Any = ai_analysis.get(
        "points",
        []
    )

    if not isinstance(
        raw_points,
        list
    ):
        return []

    typed_points = cast(
        list[Any],
        raw_points
    )

    points: list[
        dict[str, Any]
    ] = []

    for raw_point in typed_points:

        if not isinstance(
            raw_point,
            dict
        ):
            continue

        point = cast(
            dict[str, Any],
            raw_point
        )

        points.append(
            point
        )

    return points


def get_valid_regulations(
    raw_regulations: Any,
) -> list[dict[str, Any]]:
    """
    Safely validate retrieved
    Bahrain regulations.
    """

    if not isinstance(
        raw_regulations,
        list
    ):
        return []

    typed_regulations = cast(
        list[Any],
        raw_regulations
    )

    regulations: list[
        dict[str, Any]
    ] = []

    for raw_regulation in typed_regulations:

        if not isinstance(
            raw_regulation,
            dict
        ):
            continue

        regulation = cast(
            dict[str, Any],
            raw_regulation
        )

        regulations.append(
            regulation
        )

    return regulations


@router.post("/document")
async def analyze_document(
    file: UploadFile = File(...)
) -> dict[str, Any]:
    """
    Complete Analyze Document pipeline:

    1. Read uploaded document.
    2. Extract document text.
    3. Use AI to understand the document.
    4. Extract meaningful document points.
    5. Retrieve relevant Bahrain regulations.
    6. Compare each point with retrieved laws.
    7. Return the complete legal analysis.
    """

    try:

        filename = file.filename

        if not filename:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Uploaded file must "
                    "have a filename."
                ),
            )

        # ---------------------------------
        # 1. Read uploaded file
        # ---------------------------------

        content = await file.read()

        # ---------------------------------
        # 2. Extract document text
        # ---------------------------------

        result: DocumentResult = (
            extract_document_text(
                filename=filename,
                content=content,
            )
        )

        # ---------------------------------
        # 3. AI reads the document
        # ---------------------------------

        ai_analysis = (
            analyze_document_text(
                document_text=result[
                    "text"
                ]
            )
        )

        # ---------------------------------
        # 4. Validate extracted points
        # ---------------------------------

        points = get_valid_points(
            ai_analysis
        )

        # ---------------------------------
        # 5. Retrieve Bahrain laws
        # ---------------------------------

        legal_retrieval = (
            retrieve_laws_for_points(
                points=points,
                limit_per_point=5,
            )
        )

        # ---------------------------------
        # 6. Legal comparison
        # ---------------------------------

        legal_analysis: list[
            dict[str, Any]
        ] = []

        for item in legal_retrieval:

            raw_point: Any = item.get(
                "point",
                {}
            )

            if not isinstance(
                raw_point,
                dict
            ):
                continue

            point = cast(
                dict[str, Any],
                raw_point
            )

            raw_regulations: Any = (
                item.get(
                    "regulations",
                    []
                )
            )

            regulations = (
                get_valid_regulations(
                    raw_regulations
                )
            )

            comparison = (
                compare_point_with_regulations(
                    point=point,
                    regulations=regulations,
                )
            )

            legal_analysis.append(
                {
                    "point": point,
                    "retrieved_regulations": (
                        regulations
                    ),
                    "comparison": comparison,
                }
            )

        # ---------------------------------
        # 7. Return final result
        # ---------------------------------

        return {
            "success": True,
            "message": (
                "Document analyzed successfully."
            ),
            "document": {
                "filename": result[
                    "filename"
                ],
                "file_type": result[
                    "file_type"
                ],
                "file_size": result[
                    "file_size"
                ],
                "characters": result[
                    "characters"
                ],
            },
            "analysis": ai_analysis,
            "legal_analysis": (
                legal_analysis
            ),
        }

    except HTTPException:
        raise

    except DocumentProcessingError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Document analysis failed: "
                f"{str(exc)}"
            ),
        ) from exc

    finally:
        await file.close()