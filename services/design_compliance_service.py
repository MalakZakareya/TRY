import json
from typing import Any, cast

from openai import OpenAI

from core.config import settings


class DesignComplianceError(Exception):
    pass


client = OpenAI(
    api_key=settings.OPENAI_API_KEY
)


ALLOWED_STATUSES = {
    "PASS",
    "ISSUE",
    "WARNING",
    "NOT VERIFIED",
}


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


def build_compliance_prompt(
    observations: list[dict[str, Any]],
    nea_requirements: list[dict[str, Any]],
) -> str:
    observations_json = json.dumps(
        observations,
        ensure_ascii=False,
        indent=2,
    )

    requirements_json = json.dumps(
        nea_requirements,
        ensure_ascii=False,
        indent=2,
    )

    return f"""
You are reviewing a website or mobile application
UI design against retrieved Bahrain NEA requirements.

You must use ONLY:
1. The visual observations provided below.
2. The retrieved NEA requirements provided below.

Do not invent requirements.
Do not use requirements that were not provided.
Do not claim that something is visible unless it
appears in the visual observations.

For each relevant NEA requirement, determine one
of these statuses:

PASS:
The visual evidence clearly shows that the
requirement is satisfied.

ISSUE:
The visual evidence clearly shows a conflict
with the requirement.

WARNING:
There is visible evidence of a possible concern,
but the evidence is not sufficient for a definite
ISSUE.

NOT VERIFIED:
The requirement cannot be reliably checked from
the supplied visual design alone.

Important:
Technical or runtime requirements that cannot be
verified from a screenshot or design image must
be NOT VERIFIED.

For every result:
- preserve the NEA section number
- preserve the NEA title
- explain the observed evidence
- explain the comparison
- provide a recommendation when useful
- preserve the official source URL
- never invent a source

VISUAL OBSERVATIONS:

{observations_json}

RETRIEVED NEA REQUIREMENTS:

{requirements_json}

Return valid JSON only in this exact structure:

{{
  "results": [
    {{
      "section_number": "4.20",
      "title": "Colors",
      "status": "PASS",
      "observed_evidence": "Visible evidence",
      "analysis": "Comparison with the requirement",
      "recommendation": "Recommendation",
      "source_url": "official source URL"
    }}
  ]
}}
"""


def validate_compliance_results(
    raw_results: Any,
) -> list[dict[str, Any]]:
    if not isinstance(
        raw_results,
        list,
    ):
        raise DesignComplianceError(
            "AI returned an invalid "
            "compliance results list."
        )

    validated: list[
        dict[str, Any]
    ] = []

    for raw_item in cast(
        list[Any],
        raw_results,
    ):
        if not isinstance(
            raw_item,
            dict,
        ):
            continue

        item = cast(
            dict[str, Any],
            raw_item,
        )

        section_number = str(
            item.get(
                "section_number",
                "",
            )
        ).strip()

        title = str(
            item.get(
                "title",
                "",
            )
        ).strip()

        status = str(
            item.get(
                "status",
                "NOT VERIFIED",
            )
        ).strip().upper()

        observed_evidence = str(
            item.get(
                "observed_evidence",
                "",
            )
        ).strip()

        analysis = str(
            item.get(
                "analysis",
                "",
            )
        ).strip()

        recommendation = str(
            item.get(
                "recommendation",
                "",
            )
        ).strip()

        source_url = str(
            item.get(
                "source_url",
                "",
            )
        ).strip()

        if status not in ALLOWED_STATUSES:
            status = "NOT VERIFIED"

        if not section_number:
            continue

        validated.append(
            {
                "section_number": (
                    section_number
                ),
                "title": title,
                "status": status,
                "observed_evidence": (
                    observed_evidence
                ),
                "analysis": analysis,
                "recommendation": (
                    recommendation
                ),
                "source_url": source_url,
            }
        )

    return validated


def get_test_compliance_results(
    observations: list[dict[str, Any]],
    nea_requirements: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Build mock compliance results from the REAL
    NEA requirements retrieved from the knowledge base.

    No OpenAI API request is made.
    """

    results: list[dict[str, Any]] = []

    statuses = [
        "PASS",
        "WARNING",
        "NOT VERIFIED",
        "PASS",
        "ISSUE",
    ]

    for index, requirement in enumerate(
        nea_requirements[:5]
    ):
        section_number = str(
            requirement.get(
                "section_number",
                "",
            )
        ).strip()

        title = str(
            requirement.get(
                "title",
                "NEA Requirement",
            )
        ).strip()

        source_url = str(
            requirement.get(
                "source_url",
                "",
            )
        ).strip()

        if not section_number:
            continue

        status = statuses[
            index % len(statuses)
        ]

        if observations:
            observed_evidence = str(
                observations[
                    index % len(observations)
                ].get(
                    "observation",
                    "Test-mode visual observation.",
                )
            )
        else:
            observed_evidence = (
                "No visual observation was "
                "available for this requirement."
            )

        if status == "PASS":
            analysis = (
                "Test mode: the visible design "
                "evidence is being treated as "
                "consistent with this retrieved "
                "NEA requirement."
            )

            recommendation = (
                "Maintain the current design "
                "approach and verify again in "
                "real AI mode."
            )

        elif status == "ISSUE":
            analysis = (
                "Test mode: this result simulates "
                "a visible conflict with the "
                "retrieved NEA requirement."
            )

            recommendation = (
                "Review this design element "
                "against the cited NEA requirement."
            )

        elif status == "WARNING":
            analysis = (
                "Test mode: the visual evidence "
                "suggests a possible concern but "
                "is not sufficient for a definite "
                "issue."
            )

            recommendation = (
                "Review the element manually and "
                "confirm it in real AI mode."
            )

        else:
            analysis = (
                "Test mode: this requirement "
                "cannot be reliably verified from "
                "the available visual evidence."
            )

            recommendation = (
                "Verify this requirement through "
                "implementation or runtime testing."
            )

        results.append(
            {
                "section_number": (
                    section_number
                ),
                "title": title,
                "status": status,
                "observed_evidence": (
                    observed_evidence
                ),
                "analysis": analysis,
                "recommendation": (
                    recommendation
                ),
                "source_url": source_url,
            }
        )

    return results


def analyze_design_compliance(
    observations: list[dict[str, Any]],
    nea_requirements: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not nea_requirements:
        return []

    # ---------------------------------------------------------
    # TEST MODE
    # ---------------------------------------------------------
    if settings.TEST_MODE:
        return get_test_compliance_results(
            observations=observations,
            nea_requirements=nea_requirements,
        )

    # ---------------------------------------------------------
    # REAL OPENAI MODE
    # ---------------------------------------------------------

    prompt = build_compliance_prompt(
        observations=observations,
        nea_requirements=nea_requirements,
    )

    try:
        response = client.responses.create(
            model="gpt-5.6",
            input=prompt,
        )

        output_text = response.output_text

        if not output_text:
            raise DesignComplianceError(
                "AI returned an empty "
                "compliance analysis."
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
            raise DesignComplianceError(
                "AI returned invalid "
                "compliance JSON."
            )

        parsed = cast(
            dict[str, Any],
            parsed_raw,
        )

        raw_results: Any = parsed.get(
            "results",
            [],
        )

        return validate_compliance_results(
            raw_results
        )

    except DesignComplianceError:
        raise

    except json.JSONDecodeError as exc:
        raise DesignComplianceError(
            "AI returned invalid JSON "
            "for compliance analysis."
        ) from exc

    except Exception as exc:
        raise DesignComplianceError(
            "AI design compliance analysis "
            f"failed: {str(exc)}"
        ) from exc