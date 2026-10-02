import json
from typing import Any, cast

from openai import OpenAI

from core.config import settings
from services.legal_retriever import search_regulations


client = OpenAI(
    api_key=settings.OPENAI_API_KEY
)


ALLOWED_STATUSES = {
    "PASS",
    "ISSUE",
    "WARNING",
    "NOT VERIFIED",
}


def retrieve_laws_for_point(
    point: dict[str, Any],
    limit: int = 5,
) -> dict[str, Any]:
    """
    Find the most relevant Bahrain regulations
    for one extracted document point.

    This step works locally and does not call OpenAI.
    """

    title = str(
        point.get("title", "")
    ).strip()

    category = str(
        point.get("category", "")
    ).strip()

    original_text = str(
        point.get("original_text", "")
    ).strip()

    explanation = str(
        point.get("explanation", "")
    ).strip()

    query_parts = [
        title,
        category,
        original_text,
        explanation,
    ]

    query = " ".join(
        part
        for part in query_parts
        if part
    ).strip()

    if not query:
        return {
            "point": point,
            "search_query": "",
            "regulations": [],
        }

    regulations = search_regulations(
        query=query,
        limit=limit,
    )

    return {
        "point": point,
        "search_query": query,
        "regulations": regulations,
    }


def retrieve_laws_for_points(
    points: list[dict[str, Any]],
    limit_per_point: int = 5,
) -> list[dict[str, Any]]:
    """
    Find relevant Bahrain regulations
    for every point extracted from a document.
    """

    results: list[
        dict[str, Any]
    ] = []

    for point in points:

        result = retrieve_laws_for_point(
            point=point,
            limit=limit_per_point,
        )

        results.append(
            result
        )

    return results


def build_legal_sources(
    regulations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Build the trusted legal source package
    that will be provided to the AI.
    """

    legal_sources: list[
        dict[str, Any]
    ] = []

    for regulation in regulations:

        legal_sources.append(
            {
                "source_id": regulation.get(
                    "source_id",
                    ""
                ),
                "title": regulation.get(
                    "title",
                    ""
                ),
                "law_number": regulation.get(
                    "law_number",
                    ""
                ),
                "year": regulation.get(
                    "year",
                    ""
                ),
                "article": regulation.get(
                    "article",
                    ""
                ),
                "text": regulation.get(
                    "text",
                    ""
                ),
                "source_url": regulation.get(
                    "source_url",
                    ""
                ),
            }
        )

    return legal_sources


def get_allowed_article_keys(
    legal_sources: list[dict[str, Any]],
) -> set[tuple[str, str, str]]:
    """
    Build a set of legal article identifiers
    that were actually supplied to the AI.
    """

    allowed: set[
        tuple[str, str, str]
    ] = set()

    for source in legal_sources:

        law_number = str(
            source.get(
                "law_number",
                ""
            )
        ).strip()

        year = str(
            source.get(
                "year",
                ""
            )
        ).strip()

        article = str(
            source.get(
                "article",
                ""
            )
        ).strip()

        allowed.add(
            (
                law_number,
                year,
                article,
            )
        )

    return allowed


def validate_legal_analysis(
    result: dict[str, Any],
    legal_sources: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Validate the AI legal analysis.

    Prevent unsupported statuses and remove
    article references that were not supplied
    by the legal retriever.
    """

    status = str(
        result.get(
            "status",
            "NOT VERIFIED"
        )
    ).strip().upper()

    if status not in ALLOWED_STATUSES:
        status = "NOT VERIFIED"

    explanation = str(
        result.get(
            "explanation",
            ""
        )
    ).strip()

    recommendation = str(
        result.get(
            "recommendation",
            ""
        )
    ).strip()

    raw_articles_value: Any = (
        result.get(
            "relevant_articles",
            []
        )
    )

    raw_articles: list[Any]

    if isinstance(
        raw_articles_value,
        list
    ):
        raw_articles = cast(
            list[Any],
            raw_articles_value
        )
    else:
        raw_articles = []

    allowed_article_keys = (
        get_allowed_article_keys(
            legal_sources
        )
    )

    validated_articles: list[
        dict[str, Any]
    ] = []

    for raw_article in raw_articles:

        if not isinstance(
            raw_article,
            dict
        ):
            continue

        article_data = cast(
            dict[str, Any],
            raw_article
        )

        law_number = str(
            article_data.get(
                "law_number",
                ""
            )
        ).strip()

        year = str(
            article_data.get(
                "year",
                ""
            )
        ).strip()

        article = str(
            article_data.get(
                "article",
                ""
            )
        ).strip()

        article_key = (
            law_number,
            year,
            article,
        )

        if (
            article_key
            not in allowed_article_keys
        ):
            continue

        matching_source = next(
            (
                source
                for source in legal_sources
                if (
                    str(
                        source.get(
                            "law_number",
                            ""
                        )
                    ).strip()
                    == law_number
                    and str(
                        source.get(
                            "year",
                            ""
                        )
                    ).strip()
                    == year
                    and str(
                        source.get(
                            "article",
                            ""
                        )
                    ).strip()
                    == article
                )
            ),
            None,
        )

        if matching_source is None:
            continue

        validated_articles.append(
            {
                "law_number": law_number,
                "year": year,
                "article": article,
                "source_url": str(
                    matching_source.get(
                        "source_url",
                        ""
                    )
                ).strip(),
                "reason": str(
                    article_data.get(
                        "reason",
                        ""
                    )
                ).strip(),
            }
        )

    # PASS / ISSUE / WARNING must have at least
    # one verified article from the supplied sources.
    if (
        status
        in {
            "PASS",
            "ISSUE",
            "WARNING",
        }
        and not validated_articles
    ):
        status = "NOT VERIFIED"

        if not explanation:
            explanation = (
                "The supplied legal provisions "
                "were not sufficient to verify "
                "this point."
            )

    if (
        status == "NOT VERIFIED"
        and not recommendation
    ):
        recommendation = (
            "This point requires further "
            "legal verification."
        )

    return {
        "status": status,
        "explanation": explanation,
        "relevant_articles": validated_articles,
        "recommendation": recommendation,
    }


def compare_point_with_regulations(
    point: dict[str, Any],
    regulations: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Compare one document point with retrieved
    Bahrain regulations using AI.

    The AI must use only the regulations
    supplied to it.
    """

    if not regulations:
        return {
            "status": "NOT VERIFIED",
            "explanation": (
                "No relevant Bahrain regulation "
                "was retrieved for this point."
            ),
            "relevant_articles": [],
            "recommendation": (
                "This point requires further "
                "legal verification."
            ),
        }

    legal_sources = build_legal_sources(
        regulations
    )

    prompt = f"""
You are analyzing one point from a document
against retrieved Bahrain legal provisions.

IMPORTANT RULES:

- Use ONLY the Bahrain legal provisions supplied below.
- Do NOT invent laws, articles, requirements or legal conclusions.
- Do NOT rely on legal information that is not provided below.
- A retrieved article may be irrelevant even if it contains similar words.
- Carefully determine whether each retrieved article is actually relevant.
- Ignore retrieved provisions that are not genuinely relevant.
- If the supplied provisions are insufficient to verify the document point,
  return NOT VERIFIED.
- Preserve law numbers, years, article numbers and source URLs exactly.
- Do not cite an article unless it appears in the supplied provisions.
- Explain the reasoning clearly and conservatively.

Allowed status values:

PASS
The document point appears consistent with
the supplied relevant provisions.

ISSUE
The document point appears to conflict with
a supplied relevant provision.

WARNING
There is a potential concern, ambiguity,
missing condition, or qualification that
should be reviewed.

NOT VERIFIED
The supplied provisions are not sufficient
to verify the point.

DOCUMENT POINT:

{json.dumps(
    point,
    ensure_ascii=False,
    indent=2
)}

RETRIEVED BAHRAIN LEGAL PROVISIONS:

{json.dumps(
    legal_sources,
    ensure_ascii=False,
    indent=2
)}

Return ONLY valid JSON using exactly this structure:

{{
    "status": "PASS | ISSUE | WARNING | NOT VERIFIED",
    "explanation": "",
    "relevant_articles": [
        {{
            "law_number": "",
            "year": "",
            "article": "",
            "source_url": "",
            "reason": ""
        }}
    ],
    "recommendation": ""
}}
"""

    response = client.responses.create(
        model="gpt-5.6",
        input=prompt,
    )

    result_text = (
        response.output_text.strip()
    )

    if result_text.startswith(
        "```json"
    ):
        result_text = result_text[
            7:
        ]

    if result_text.startswith(
        "```"
    ):
        result_text = result_text[
            3:
        ]

    if result_text.endswith(
        "```"
    ):
        result_text = result_text[
            :-3
        ]

    result_text = (
        result_text.strip()
    )

    try:

        raw_result: Any = json.loads(
            result_text
        )

    except json.JSONDecodeError as exc:

        raise ValueError(
            "The AI returned an invalid legal "
            "analysis JSON response."
        ) from exc

    if not isinstance(
        raw_result,
        dict
    ):
        raise ValueError(
            "The AI returned an invalid legal "
            "analysis response."
        )

    result = cast(
        dict[str, Any],
        raw_result
    )

    return validate_legal_analysis(
        result=result,
        legal_sources=legal_sources,
    )