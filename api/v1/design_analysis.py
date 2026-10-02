from typing import Any, cast

from fastapi import (
    APIRouter,
    File,
    HTTPException,
    UploadFile,
)

from services.design_service import (
    DesignProcessingError,
    DesignResult,
    prepare_design_images,
    process_design_file,
)

from services.design_vision_service import (
    DesignVisionError,
    analyze_design_images,
)

from services.nea_retriever import (
    retrieve_design_requirements,
)

from services.design_compliance_service import (
    DesignComplianceError,
    analyze_design_compliance,
)


router = APIRouter(
    prefix="/api/v1/design",
    tags=["Design Analysis"],
)


@router.post("/analyze")
async def analyze_design(
    file: UploadFile = File(...),
) -> dict[str, Any]:

    try:
        filename = file.filename

        if not filename:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Uploaded design must "
                    "have a filename."
                ),
            )

        content = await file.read()

        # Step 1:
        # Validate and prepare the uploaded design.
        result: DesignResult = process_design_file(
            filename=filename,
            content=content,
        )

        design_images = prepare_design_images(
            filename=filename,
            content=content,
        )

        # Step 2:
        # AI visually inspects the actual design.
        vision_result = analyze_design_images(
            design_images=design_images,
        )

        detected_raw: Any = vision_result.get(
            "detected_elements",
            [],
        )

        observations_raw: Any = vision_result.get(
            "observations",
            [],
        )

        detected_elements: list[str] = []

        if isinstance(
            detected_raw,
            list,
        ):
            for item in cast(
                list[Any],
                detected_raw,
            ):
                if isinstance(
                    item,
                    str,
                ):
                    detected_elements.append(
                        item
                    )

        observations: list[
            dict[str, Any]
        ] = []

        if isinstance(
            observations_raw,
            list,
        ):
            for item in cast(
                list[Any],
                observations_raw,
            ):
                if isinstance(
                    item,
                    dict,
                ):
                    observations.append(
                        cast(
                            dict[str, Any],
                            item,
                        )
                    )

        # Step 3:
        # Retrieve only relevant official
        # NEA requirements.
        nea_requirements = (
            retrieve_design_requirements(
                detected_elements=detected_elements,
                limit_per_element=3,
            )
        )

        # Step 4:
        # Compare the visual observations
        # against the retrieved requirements.
        compliance_results = (
            analyze_design_compliance(
                observations=observations,
                nea_requirements=nea_requirements,
            )
        )

        # Step 5:
        # Calculate report status counts.
        status_counts = {
            "PASS": 0,
            "ISSUE": 0,
            "WARNING": 0,
            "NOT VERIFIED": 0,
        }

        for item in compliance_results:
            status = str(
                item.get(
                    "status",
                    "NOT VERIFIED",
                )
            ).upper()

            if status in status_counts:
                status_counts[status] += 1

        return {
            "success": True,
            "message": (
                "Design review completed "
                "successfully."
            ),
            "design": {
                "filename": result["filename"],
                "file_type": result["file_type"],
                "file_size": result["file_size"],
                "page_count": result["page_count"],
                "content_type": result["content_type"],
                "prepared_images": len(
                    design_images
                ),
            },
            "vision_analysis": {
                "detected_elements": (
                    detected_elements
                ),
                "observations": (
                    observations
                ),
            },
            "nea_requirements_count": len(
                nea_requirements
            ),
            "compliance_report": {
                "total": len(
                    compliance_results
                ),
                "status_counts": (
                    status_counts
                ),
                "results": (
                    compliance_results
                ),
            },
        }

    except HTTPException:
        raise

    except DesignProcessingError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except DesignVisionError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc

    except DesignComplianceError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Design analysis failed: "
                f"{str(exc)}"
            ),
        ) from exc

    finally:
        await file.close()