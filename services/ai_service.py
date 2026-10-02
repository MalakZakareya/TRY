import json
from typing import Any

from openai import OpenAI

from core.config import settings


client = OpenAI(api_key=settings.OPENAI_API_KEY)


def analyze_document_text(document_text: str) -> dict[str, Any]:
    """
    Read the extracted document text and identify its important
    clauses, requirements, obligations, rights, dates, amounts,
    conditions, and other meaningful points.

    This step does NOT perform Bahrain legal compliance checking yet.
    """

    if not document_text.strip():
        raise ValueError("Document text is empty.")

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

    response = client.responses.create(
        model="gpt-5.6",
        input=prompt,
    )

    result_text = response.output_text.strip()

    # Remove Markdown fences if the model returned them.
    if result_text.startswith("```json"):
        result_text = result_text[7:]

    if result_text.startswith("```"):
        result_text = result_text[3:]

    if result_text.endswith("```"):
        result_text = result_text[:-3]

    result_text = result_text.strip()

    try:
        return json.loads(result_text)

    except json.JSONDecodeError as exc:
        raise ValueError(
            "The AI returned an invalid JSON response."
        ) from exc