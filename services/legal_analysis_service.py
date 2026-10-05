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


# ---------------------------------------------------------
# Point-specific legal search expansion
# ---------------------------------------------------------

POINT_SEARCH_QUERIES: dict[str, list[str]] = {
    "employment": [
        "employment contract",
        "employment relationship",
        "عقد العمل",
        "عقد العمل الفردي",
        "بيانات عقد العمل",
    ],
    "salary": [
        "salary wages payment",
        "wages salary payment",
        "الأجر",
        "الأجور",
        "أداء الأجور",
    ],
    "working_hours": [
        "working hours",
        "rest periods",
        "overtime work",
        "ساعات العمل",
        "فترات الراحة",
        "العمل الإضافي",
    ],
    "annual_leave": [
        "annual leave",
        "annual holiday",
        "الإجازة السنوية",
        "الإجازات السنوية",
    ],
    "sick_leave": [
        "sick leave",
        "الإجازة المرضية",
    ],
    "termination": [
        "termination employment",
        "notice period",
        "termination notice",
        "إنهاء عقد العمل",
        "إنهاء العقد",
        "مهلة الإخطار",
    ],
    "probation": [
        "probation period",
        "employment probation",
        "فترة التجربة",
        "شرط التجربة",
    ],
    "confidentiality": [
        "confidentiality personal data",
        "employee personal data",
        "سرية البيانات",
        "البيانات الشخصية",
    ],
}


def normalize_lookup_text(
    value: str,
) -> str:
    """
    Light normalization used only for determining
    the type of document point.

    This does not change stored law text.
    """

    return (
        value
        .strip()
        .lower()
        .replace("_", " ")
        .replace("-", " ")
    )


def detect_point_search_group(
    point: dict[str, Any],
) -> str:
    """
    Determine which legal-search group best matches
    the extracted document point.
    """

    title = normalize_lookup_text(
        str(
            point.get(
                "title",
                "",
            )
        )
    )

    category = normalize_lookup_text(
        str(
            point.get(
                "category",
                "",
            )
        )
    )

    combined = (
        title
        + " "
        + category
    ).strip()

    if (
        "employment relationship" in combined
        or "employment contract" in combined
        or "employment" == category
        or "عقد العمل" in combined
    ):
        return "employment"

    if (
        "salary" in combined
        or "wage" in combined
        or "compensation" in combined
        or "أجر" in combined
        or "راتب" in combined
    ):
        return "salary"

    if (
        "working hour" in combined
        or "overtime" in combined
        or "working hours" in category
        or "ساعات العمل" in combined
        or "عمل إضافي" in combined
    ):
        return "working_hours"

    if (
        "annual leave" in combined
        or "annual holiday" in combined
        or "إجازة سنوية" in combined
        or "الاجازة السنوية" in combined
    ):
        return "annual_leave"

    if (
        "sick leave" in combined
        or "إجازة مرضية" in combined
        or "الاجازة المرضية" in combined
    ):
        return "sick_leave"

    if (
        "termination" in combined
        or "notice" in combined
        or "إنهاء" in combined
        or "اخطار" in combined
        or "إخطار" in combined
    ):
        return "termination"

    if (
        "probation" in combined
        or "فترة التجربة" in combined
        or "شرط التجربة" in combined
    ):
        return "probation"

    if (
        "confidential" in combined
        or "personal data" in combined
        or "data protection" in combined
        or "سرية" in combined
        or "بيانات شخصية" in combined
    ):
        return "confidentiality"

    return ""


def build_regulation_key(
    regulation: dict[str, Any],
) -> str:
    """
    Build a stable key for deduplicating retrieved
    legal provisions.
    """

    regulation_id = str(
        regulation.get(
            "id",
            "",
        )
    ).strip()

    if regulation_id:
        return regulation_id

    source_id = str(
        regulation.get(
            "source_id",
            "",
        )
    ).strip()

    article = str(
        regulation.get(
            "article",
            "",
        )
    ).strip()

    title = str(
        regulation.get(
            "title",
            "",
        )
    ).strip()

    return (
        source_id
        + "|"
        + article
        + "|"
        + title
    )


def get_regulation_score(
    regulation: dict[str, Any],
) -> int:
    """
    Safely read retriever relevance score.
    """

    value: Any = regulation.get(
        "relevance_score",
        0,
    )

    try:
        return int(
            str(value)
        )
    except (
        TypeError,
        ValueError,
    ):
        return 0


def point_mentions_juvenile(
    point: dict[str, Any],
) -> bool:
    """
    Check whether the document point itself is
    specifically about juvenile employment.
    """

    point_text = " ".join(
        [
            str(
                point.get(
                    "title",
                    "",
                )
            ),
            str(
                point.get(
                    "category",
                    "",
                )
            ),
            str(
                point.get(
                    "original_text",
                    "",
                )
            ),
            str(
                point.get(
                    "explanation",
                    "",
                )
            ),
        ]
    ).lower()

    markers = [
        "juvenile",
        "minor worker",
        "young worker",
        "حدث",
        "الأحداث",
        "الاحداث",
    ]

    return any(
        marker in point_text
        for marker in markers
    )


def regulation_is_juvenile_specific(
    regulation: dict[str, Any],
) -> bool:
    """
    Detect provisions whose text is specifically
    scoped to juvenile workers.

    This is intentionally based on the provision
    text rather than hardcoding an article number.
    """

    text = " ".join(
        [
            str(
                regulation.get(
                    "title",
                    "",
                )
            ),
            str(
                regulation.get(
                    "text",
                    "",
                )
            ),
        ]
    ).lower()

    markers = [
        "juvenile",
        "juveniles",
        "minor worker",
        "young worker",
        "الحدث",
        "الأحداث",
        "الاحداث",
    ]

    return any(
        marker in text
        for marker in markers
    )


def regulation_is_applicable_to_point(
    point: dict[str, Any],
    regulation: dict[str, Any],
) -> bool:
    """
    Remove clearly special-scope provisions from
    generic document points.

    At present this protects generic employment
    analysis from juvenile-specific provisions.

    If the document point itself mentions juvenile
    employment, those provisions remain eligible.
    """

    if point_mentions_juvenile(
        point
    ):
        return True

    if regulation_is_juvenile_specific(
        regulation
    ):
        return False

    return True


def build_point_search_queries(
    point: dict[str, Any],
) -> list[str]:
    """
    Build a set of legal search queries for one
    document point.

    The original document wording is always kept.
    Topic-specific bilingual legal queries are added
    only when the point type can be identified.
    """

    title = str(
        point.get(
            "title",
            "",
        )
    ).strip()

    category = str(
        point.get(
            "category",
            "",
        )
    ).strip()

    original_text = str(
        point.get(
            "original_text",
            "",
        )
    ).strip()

    explanation = str(
        point.get(
            "explanation",
            "",
        )
    ).strip()

    original_query = " ".join(
        part
        for part in [
            title,
            category,
            original_text,
            explanation,
        ]
        if part
    ).strip()

    queries: list[str] = []

    if original_query:
        queries.append(
            original_query
        )

    search_group = (
        detect_point_search_group(
            point
        )
    )

    if search_group:
        expanded_queries = (
            POINT_SEARCH_QUERIES.get(
                search_group,
                [],
            )
        )

        for query in expanded_queries:
            clean_query = str(
                query
            ).strip()

            if (
                clean_query
                and clean_query
                not in queries
            ):
                queries.append(
                    clean_query
                )

    return queries


def retrieve_laws_for_point(
    point: dict[str, Any],
    limit: int = 5,
) -> dict[str, Any]:
    """
    Find relevant Bahrain regulations for one
    extracted document point.

    Multiple bilingual legal queries may be used
    for better retrieval accuracy.

    This step works locally and does not call OpenAI.
    """

    queries = build_point_search_queries(
        point
    )

    if not queries:
        return {
            "point": point,
            "search_query": "",
            "search_queries": [],
            "regulations": [],
        }

    # Search more broadly internally before
    # deduplication and applicability filtering.
    internal_limit = max(
        limit * 3,
        10,
    )

    candidates: dict[
        str,
        dict[str, Any],
    ] = {}

    for query in queries:

        matches = search_regulations(
            query=query,
            limit=internal_limit,
        )

        for match in matches:

            if not regulation_is_applicable_to_point(
                point=point,
                regulation=match,
            ):
                continue

            key = build_regulation_key(
                match
            )

            if not key:
                continue

            existing = candidates.get(
                key
            )

            if existing is None:
                candidate = {
                    **match
                }

                candidate[
                    "analysis_matched_queries"
                ] = [
                    query
                ]

                candidate[
                    "analysis_best_score"
                ] = get_regulation_score(
                    match
                )

                candidates[
                    key
                ] = candidate

                continue

            existing_queries_value: Any = (
                existing.get(
                    "analysis_matched_queries",
                    [],
                )
            )

            existing_queries: list[str] = []

            if isinstance(
                existing_queries_value,
                list,
            ):
                typed_queries = cast(
                    list[Any],
                    existing_queries_value,
                )

                for item in typed_queries:
                    item_text = str(
                        item
                    ).strip()

                    if (
                        item_text
                        and item_text
                        not in existing_queries
                    ):
                        existing_queries.append(
                            item_text
                        )

            if query not in existing_queries:
                existing_queries.append(
                    query
                )

            existing[
                "analysis_matched_queries"
            ] = existing_queries

            current_best_value: Any = (
                existing.get(
                    "analysis_best_score",
                    0,
                )
            )

            try:
                current_best = int(
                    str(
                        current_best_value
                    )
                )
            except (
                TypeError,
                ValueError,
            ):
                current_best = 0

            new_score = get_regulation_score(
                match
            )

            existing[
                "analysis_best_score"
            ] = max(
                current_best,
                new_score,
            )

    ranked = list(
        candidates.values()
    )

    ranked.sort(
        key=lambda regulation: (
            int(
                str(
                    regulation.get(
                        "analysis_best_score",
                        0,
                    )
                )
            ),
            len(
                cast(
                    list[Any],
                    regulation.get(
                        "analysis_matched_queries",
                        [],
                    ),
                )
            ),
        ),
        reverse=True,
    )

    selected = ranked[
        :limit
    ]

    return {
        "point": point,
        "search_query": queries[0],
        "search_queries": queries,
        "regulations": selected,
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
                    "",
                ),
                "title": regulation.get(
                    "title",
                    "",
                ),
                "law_number": regulation.get(
                    "law_number",
                    "",
                ),
                "year": regulation.get(
                    "year",
                    "",
                ),
                "article": regulation.get(
                    "article",
                    "",
                ),
                "text": regulation.get(
                    "text",
                    "",
                ),
                "source_url": regulation.get(
                    "source_url",
                    "",
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
                "",
            )
        ).strip()

        year = str(
            source.get(
                "year",
                "",
            )
        ).strip()

        article = str(
            source.get(
                "article",
                "",
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
            "NOT VERIFIED",
        )
    ).strip().upper()

    if status not in ALLOWED_STATUSES:
        status = "NOT VERIFIED"

    explanation = str(
        result.get(
            "explanation",
            "",
        )
    ).strip()

    recommendation = str(
        result.get(
            "recommendation",
            "",
        )
    ).strip()

    raw_articles_value: Any = (
        result.get(
            "relevant_articles",
            [],
        )
    )

    raw_articles: list[Any]

    if isinstance(
        raw_articles_value,
        list,
    ):
        raw_articles = cast(
            list[Any],
            raw_articles_value,
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
            dict,
        ):
            continue

        article_data = cast(
            dict[str, Any],
            raw_article,
        )

        law_number = str(
            article_data.get(
                "law_number",
                "",
            )
        ).strip()

        year = str(
            article_data.get(
                "year",
                "",
            )
        ).strip()

        article = str(
            article_data.get(
                "article",
                "",
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
                            "",
                        )
                    ).strip()
                    == law_number
                    and str(
                        source.get(
                            "year",
                            "",
                        )
                    ).strip()
                    == year
                    and str(
                        source.get(
                            "article",
                            "",
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
                        "",
                    )
                ).strip(),
                "reason": str(
                    article_data.get(
                        "reason",
                        "",
                    )
                ).strip(),
            }
        )

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


def get_test_legal_analysis(
    legal_sources: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Build a deterministic legal-analysis result
    for TEST_MODE.

    No OpenAI request is made.
    """

    test_articles: list[
        dict[str, Any]
    ] = []

    for source in legal_sources[:3]:

        test_articles.append(
            {
                "law_number": str(
                    source.get(
                        "law_number",
                        "",
                    )
                ).strip(),
                "year": str(
                    source.get(
                        "year",
                        "",
                    )
                ).strip(),
                "article": str(
                    source.get(
                        "article",
                        "",
                    )
                ).strip(),
                "source_url": str(
                    source.get(
                        "source_url",
                        "",
                    )
                ).strip(),
                "reason": (
                    "Retrieved from the trusted "
                    "Bahrain legal knowledge base "
                    "in TEST MODE."
                ),
            }
        )

    return {
        "status": "WARNING",
        "explanation": (
            "TEST MODE is enabled. Relevant Bahrain "
            "legal provisions were retrieved "
            "successfully, but OpenAI was not called "
            "to make the final legal comparison."
        ),
        "relevant_articles": test_articles,
        "recommendation": (
            "Review the retrieved Bahrain legal "
            "provisions. Enable real AI mode later "
            "for the full document-to-law comparison."
        ),
    }


def compare_point_with_regulations(
    point: dict[str, Any],
    regulations: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Compare one document point with retrieved
    Bahrain regulations.

    TEST_MODE does not call OpenAI.
    REAL MODE uses OpenAI only with trusted
    retrieved legal provisions.
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

    # ---------------------------------------------------------
    # TEST MODE
    # ---------------------------------------------------------

    if settings.TEST_MODE:

        test_result = get_test_legal_analysis(
            legal_sources
        )

        return validate_legal_analysis(
            result=test_result,
            legal_sources=legal_sources,
        )

    # ---------------------------------------------------------
    # REAL OPENAI MODE
    # ---------------------------------------------------------

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
        dict,
    ):
        raise ValueError(
            "The AI returned an invalid legal "
            "analysis response."
        )

    result = cast(
        dict[str, Any],
        raw_result,
    )

    return validate_legal_analysis(
        result=result,
        legal_sources=legal_sources,
    )