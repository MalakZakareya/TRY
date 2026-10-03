import json
from typing import Any, cast

from openai import OpenAI

from core.config import settings
from services.draft_service import (
    get_draft_type,
)


class DraftAIServiceError(Exception):
    pass


client = OpenAI(
    api_key=settings.OPENAI_API_KEY
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


def build_draft_prompt(
    draft_type: str,
    details: dict[str, Any],
    legal_requirements: list[dict[str, Any]],
) -> str:

    draft_config = get_draft_type(
        draft_type
    )

    details_json = json.dumps(
        details,
        ensure_ascii=False,
        indent=2,
    )

    legal_json = json.dumps(
        legal_requirements,
        ensure_ascii=False,
        indent=2,
    )

    return f"""
You are creating a professional legal or business
document draft for use in Bahrain.

DRAFT TYPE:
{draft_config["name"]}

USER-PROVIDED DETAILS:
{details_json}

RETRIEVED BAHRAIN LEGAL MATERIAL:
{legal_json}

IMPORTANT RULES:

1. Use the user-provided details accurately.

2. Do not invent names, dates, salaries, amounts,
   obligations, or other factual details.

3. Use ONLY the retrieved Bahrain legal material
   provided above when referring to Bahrain law.

4. Never invent a law, article number, regulation,
   authority, or legal source.

5. If the retrieved legal material does not support
   a legal statement, do not present that statement
   as a verified Bahrain legal requirement.

6. Do not claim that the document guarantees legal
   compliance.

7. Write a clear, professional, structured draft.

8. Keep placeholders clearly marked when information
   necessary for the document was not provided.

9. Do not place invented citations inside the draft.

10. Return JSON only.

Return valid JSON in exactly this structure:

{{
  "title": "Document title",
  "draft": "Full document text",
  "notes": [
    "Important note"
  ],
  "used_requirements": [
    {{
      "law_id": "exact law id from retrieved material",
      "article_number": "exact article number from retrieved material"
    }}
  ]
}}

For used_requirements:
- Include only legal provisions actually used when
  creating the draft.
- Copy law_id and article_number exactly from the
  retrieved material.
- If no retrieved provision was used, return an
  empty list.
"""


def generate_draft(
    draft_type: str,
    details: dict[str, Any],
    legal_requirements: list[dict[str, Any]],
) -> dict[str, Any]:

    prompt = build_draft_prompt(
        draft_type=draft_type,
        details=details,
        legal_requirements=legal_requirements,
    )

    try:
        response = client.responses.create(
            model="gpt-5.6",
            input=prompt,
        )

        output_text = response.output_text

        if not output_text:
            raise DraftAIServiceError(
                "AI returned an empty draft."
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
            raise DraftAIServiceError(
                "AI returned an invalid draft."
            )

        parsed = cast(
            dict[str, Any],
            parsed_raw,
        )

        title = str(
            parsed.get(
                "title",
                "",
            )
        ).strip()

        draft = str(
            parsed.get(
                "draft",
                "",
            )
        ).strip()

        if not title:
            raise DraftAIServiceError(
                "AI draft has no title."
            )

        if not draft:
            raise DraftAIServiceError(
                "AI draft has no content."
            )

        notes_raw: Any = parsed.get(
            "notes",
            [],
        )

        notes: list[str] = []

        if isinstance(
            notes_raw,
            list,
        ):
            for item in cast(
                list[Any],
                notes_raw,
            ):
                if isinstance(item, str):
                    notes.append(
                        item.strip()
                    )

        used_raw: Any = parsed.get(
            "used_requirements",
            [],
        )

        used_requirements: list[
            dict[str, str]
        ] = []

        if isinstance(
            used_raw,
            list,
        ):
            for item in cast(
                list[Any],
                used_raw,
            ):
                if not isinstance(
                    item,
                    dict,
                ):
                    continue

                requirement = cast(
                    dict[str, Any],
                    item,
                )

                law_id = str(
                    requirement.get(
                        "law_id",
                        "",
                    )
                ).strip()

                article_number = str(
                    requirement.get(
                        "article_number",
                        "",
                    )
                ).strip()

                if law_id and article_number:
                    used_requirements.append(
                        {
                            "law_id": law_id,
                            "article_number": (
                                article_number
                            ),
                        }
                    )

        return {
            "title": title,
            "draft": draft,
            "notes": notes,
            "used_requirements": (
                used_requirements
            ),
        }

    except DraftAIServiceError:
        raise

    except json.JSONDecodeError as exc:
        raise DraftAIServiceError(
            "AI returned invalid JSON."
        ) from exc

    except Exception as exc:
        raise DraftAIServiceError(
            "AI draft generation failed: "
            f"{str(exc)}"
        ) from exc