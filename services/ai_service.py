import json
from typing import Any, cast

from core.config import settings
from services.ai_provider import generate_ai_text


def get_test_analysis() -> dict[str, Any]:
    """
    Return a mock AI result when TEST_MODE is enabled.

    This allows the full document-analysis workflow
    to be tested without using AI credits.
    """

    return {
        "document_type": "Employment Contract",
        "language": "English",
        "summary": (
            "This is a test-mode document analysis result. "
            "The system successfully received and processed "
            "the uploaded document without calling an AI provider."
        ),
        "points": [
            {
                "point_number": 1,
                "title": "Employment Relationship",
                "category": "Employment",
                "original_text": (
                    "Test mode: employment relationship clause."
                ),
                "explanation": (
                    "This mock point confirms that the "
                    "document analysis workflow is working."
                ),
            },
            {
                "point_number": 2,
                "title": "Salary",
                "category": "Compensation",
                "original_text": (
                    "Test mode: salary clause."
                ),
                "explanation": (
                    "This mock point represents a salary "
                    "or compensation provision."
                ),
            },
            {
                "point_number": 3,
                "title": "Working Hours",
                "category": "Working Hours",
                "original_text": (
                    "Test mode: working hours clause."
                ),
                "explanation": (
                    "This mock point represents working "
                    "hours stated in the document."
                ),
            },
            {
                "point_number": 4,
                "title": "Annual Leave",
                "category": "Leave",
                "original_text": (
                    "Test mode: annual leave clause."
                ),
                "explanation": (
                    "This mock point represents an annual "
                    "leave provision."
                ),
            },
            {
                "point_number": 5,
                "title": "Termination",
                "category": "Termination",
                "original_text": (
                    "Test mode: termination clause."
                ),
                "explanation": (
                    "This mock point represents a "
                    "termination provision."
                ),
            },
        ],
    }


def analyze_document_text(
    document_text: str,
) -> dict[str, Any]:
    """
    Read the extracted document text and identify its important
    clauses, requirements, obligations, rights, dates, amounts,
    conditions, and other meaningful points.

    When TEST_MODE is enabled, a mock AI result is returned
    without making an external AI API request.
    """

    if not document_text.strip():
        raise ValueError(
            "Document text is empty."
        )

    # ---------------------------------------------------------
    # TEST MODE
    # ---------------------------------------------------------

    if settings.TEST_MODE:
        return get_test_analysis()

    # ---------------------------------------------------------
    # REAL AI MODE
    # ---------------------------------------------------------

    prompt = f"""
You are a careful professional document analysis assistant.

Your task is to read the ENTIRE document provided below carefully.

IMPORTANT:
- Do not perform legal compliance analysis yet.
- Do not compare the document with Bahrain laws yet.
- Do not invent information.
- Use only information that actually appears in the document.
- Preserve important numbers, dates, percentages, monetary amounts,
  names, durations, conditions, obligations and exceptions.
- Identify every meaningful clause or point.
- Do not skip a clause just because it looks repetitive.
- If something is unclear, say that it is unclear.
- The document may contain Arabic, English, or both.

First determine:
1. Document type
2. Document language
3. Short document summary

Then extract all meaningful points from the document.

For each point return:
- point_number
- title
- category
- original_text
- explanation

Return ONLY valid JSON using exactly this structure:

{{
    "document_type": "",
    "language": "",
    "summary": "",
    "points": [
        {{
            "point_number": 1,
            "title": "",
            "category": "",
            "original_text": "",
            "explanation": ""
        }}
    ]
}}

DOCUMENT:
--------------------
{document_text}
--------------------
"""

    # ---------------------------------------------------------
    # SELECTED AI PROVIDER
    # ---------------------------------------------------------

    result_text = generate_ai_text(
        prompt
    ).strip()

    # Remove Markdown fences if the model returned them.
    if result_text.startswith("```json"):
        result_text = result_text[7:]

    if result_text.startswith("```"):
        result_text = result_text[3:]

    if result_text.endswith("```"):
        result_text = result_text[:-3]

    result_text = result_text.strip()

    try:
        parsed_result: Any = json.loads(
            result_text
        )

        if not isinstance(
            parsed_result,
            dict,
        ):
            raise ValueError(
                "The AI returned an invalid JSON structure."
            )

        return cast(
            dict[str, Any],
            parsed_result,
        )

    except json.JSONDecodeError as exc:
        raise ValueError(
            "The AI returned an invalid JSON response."
        ) from exc