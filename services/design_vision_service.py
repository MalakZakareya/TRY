import base64
import json
from typing import Any, cast

from openai import OpenAI

from core.config import settings


class DesignVisionError(Exception):
    pass


client = OpenAI(
    api_key=settings.OPENAI_API_KEY
)


def image_bytes_to_data_url(
    image_bytes: bytes,
) -> str:
    encoded = base64.b64encode(
        image_bytes
    ).decode("utf-8")

    return (
        "data:image/png;base64,"
        + encoded
    )


def clean_json_response(
    text: str,
) -> str:
    cleaned = text.strip()

    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]

    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]

    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]

    return cleaned.strip()


def get_test_design_analysis(
    page_count: int,
) -> dict[str, Any]:
    """
    Return mock visual observations when TEST_MODE
    is enabled.

    No OpenAI API request is made.
    """

    observations: list[dict[str, Any]] = [
        {
            "element": "logo",
            "observation": (
                "A logo is visible in the header area."
            ),
            "page": 1,
        },
        {
            "element": "navigation",
            "observation": (
                "A primary navigation area is visible."
            ),
            "page": 1,
        },
        {
            "element": "colors",
            "observation": (
                "The interface uses a consistent "
                "visual color scheme."
            ),
            "page": 1,
        },
        {
            "element": "color contrast",
            "observation": (
                "Text and interface elements use "
                "visually distinguishable colors."
            ),
            "page": 1,
        },
        {
            "element": "links",
            "observation": (
                "Link-style interface elements "
                "are visible."
            ),
            "page": 1,
        },
    ]

    if page_count > 1:
        observations.append(
            {
                "element": "text",
                "observation": (
                    f"The uploaded design contains "
                    f"{page_count} prepared pages."
                ),
                "page": 2,
            }
        )

    return {
        "detected_elements": [
            "logo",
            "navigation",
            "colors",
            "color contrast",
            "links",
        ],
        "observations": observations,
    }


def analyze_design_images(
    design_images: list[bytes],
) -> dict[str, Any]:
    if not design_images:
        raise DesignVisionError(
            "No design images were provided."
        )

    # ---------------------------------------------------------
    # TEST MODE
    # ---------------------------------------------------------
    if settings.TEST_MODE:
        return get_test_design_analysis(
            page_count=len(design_images)
        )

    # ---------------------------------------------------------
    # REAL OPENAI VISION MODE
    # ---------------------------------------------------------

    prompt = """
You are analyzing website or mobile application
UI designs for a Bahrain NEA standards review.

Carefully inspect the provided design image or images.

Identify only elements that are actually visible
or reasonably observable in the design.

Look for elements such as:
- logo and branding
- header
- navigation
- footer
- links
- colors
- color contrast
- text and typography
- images
- buttons
- forms
- form fields
- labels
- search
- language selection
- breadcrumbs
- accessibility-related visual elements
- error messages
- social media elements

Do not claim that an element exists if it cannot
be observed in the supplied design.

Do not decide whether the design complies with
NEA standards yet.

Your task at this stage is only visual inspection.

Return valid JSON only in this exact structure:

{
  "detected_elements": [
    "element"
  ],
  "observations": [
    {
      "element": "element",
      "observation": "what is visibly observed",
      "page": 1
    }
  ]
}

Use short lowercase English terms in
detected_elements because they will be used
to search a standards knowledge base.

If something cannot be determined visually,
do not invent it.
"""

    content: list[Any] = [
        {
            "type": "input_text",
            "text": prompt,
        }
    ]

    for image_bytes in design_images:
        data_url = image_bytes_to_data_url(
            image_bytes
        )

        content.append(
            {
                "type": "input_image",
                "image_url": data_url,
                "detail": "high",
            }
        )

    try:
        response = client.responses.create(
            model="gpt-5.6",
            input=[
                {
                    "role": "user",
                    "content": content,
                }
            ],
        )

        output_text = response.output_text

        if not output_text:
            raise DesignVisionError(
                "AI returned an empty "
                "design analysis."
            )

        cleaned = clean_json_response(
            output_text
        )

        parsed_raw: Any = json.loads(
            cleaned
        )

        if not isinstance(
            parsed_raw,
            dict,
        ):
            raise DesignVisionError(
                "AI returned an invalid "
                "design analysis."
            )

        parsed = cast(
            dict[str, Any],
            parsed_raw,
        )

        detected_raw: Any = parsed.get(
            "detected_elements",
            [],
        )

        observations_raw: Any = parsed.get(
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

        return {
            "detected_elements": (
                detected_elements
            ),
            "observations": observations,
        }

    except DesignVisionError:
        raise

    except json.JSONDecodeError as exc:
        raise DesignVisionError(
            "AI returned invalid JSON."
        ) from exc

    except Exception as exc:
        raise DesignVisionError(
            "AI design vision analysis "
            f"failed: {str(exc)}"
        ) from exc