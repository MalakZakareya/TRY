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
# Batch configuration
# ---------------------------------------------------------

LEGAL_BATCH_SIZE = 8


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


def get_not_verified_analysis(
    explanation: str = (
        "No relevant Bahrain regulation "
        "was retrieved for this point."
    ),
) -> dict[str, Any]:
    """
    Return a safe result when a point cannot
    be legally verified.
    """

    return {
        "status": "NOT VERIFIED",
        "explanation": explanation,
        "relevant_articles": [],
        "recommendation": (
            "This point requires further "
            "legal verification."
        ),
    }


def clean_json_response(
    result_text: str,
) -> str:
    """
    Remove optional Markdown JSON fences.
    """

    cleaned = result_text.strip()

    if cleaned.startswith(
        "```json"
    ):
        cleaned = cleaned[7:]

    elif cleaned.startswith(
        "```"
    ):
        cleaned = cleaned[3:]

    if cleaned.endswith(
        "```"
    ):
        cleaned = cleaned[:-3]

    return cleaned.strip()


def compare_point_with_regulations(
    point: dict[str, Any],
    regulations: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Compare one document point with retrieved
    Bahrain regulations.

    Kept for compatibility with any other part
    of the application that uses single-point
    legal analysis.

    Analyze Document will use the batch function
    below for much better performance.
    """

    if not regulations:
        return get_not_verified_analysis()

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

    result_text = clean_json_response(
        response.output_text
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


# ---------------------------------------------------------
# Batch legal analysis
# ---------------------------------------------------------

def build_batch_item(
    batch_id: int,
    point: dict[str, Any],
    regulations: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Build one isolated item for a batch request.

    Every point receives only its own retrieved
    Bahrain legal provisions.
    """

    return {
        "batch_id": batch_id,
        "point": point,
        "legal_provisions": build_legal_sources(
            regulations
        ),
    }


def parse_batch_results(
    raw_result: Any,
) -> list[dict[str, Any]]:
    """
    Safely extract the results array returned
    by the batch OpenAI request.
    """

    if not isinstance(
        raw_result,
        dict,
    ):
        raise ValueError(
            "The AI returned an invalid batch "
            "legal analysis response."
        )

    typed_result = cast(
        dict[str, Any],
        raw_result,
    )

    raw_results_value: Any = (
        typed_result.get(
            "results",
            [],
        )
    )

    if not isinstance(
        raw_results_value,
        list,
    ):
        raise ValueError(
            "The AI batch legal analysis "
            "did not return a results list."
        )

    raw_results = cast(
        list[Any],
        raw_results_value,
    )

    valid_results: list[
        dict[str, Any]
    ] = []

    for raw_item in raw_results:
        if not isinstance(
            raw_item,
            dict,
        ):
            continue

        valid_results.append(
            cast(
                dict[str, Any],
                raw_item,
            )
        )

    return valid_results


def analyze_legal_batch(
    batch_items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Analyze several independent document points
    in one OpenAI request.

    Each point remains isolated from the other
    points and may only use its own legal_provisions.
    """

    if not batch_items:
        return []

    prompt = f"""
You are performing a careful legal comparison
of multiple independent document points against
retrieved Bahrain legal provisions.

You will receive a JSON array named BATCH ITEMS.

Each item contains:

- batch_id
- point
- legal_provisions

CRITICAL RULES:

1. Analyze EACH batch item independently.

2. For each item, use ONLY the legal_provisions
   contained inside THAT SAME item.

3. Never use a legal provision belonging to one
   batch item to analyze another batch item.

4. Do NOT invent Bahrain laws, articles,
   requirements, legal rules, or source URLs.

5. Do NOT rely on legal knowledge that is not
   explicitly provided in the item's
   legal_provisions.

6. A retrieved provision may be irrelevant even
   when it contains similar words. Determine
   actual relevance carefully.

7. Ignore retrieved provisions that are not
   genuinely relevant to the document point.

8. If the supplied provisions are insufficient
   to verify a point, return NOT VERIFIED.

9. Preserve law_number, year, article and
   source_url exactly as supplied.

10. Never cite an article unless it appears in
    the legal_provisions for that same item.

11. Be conservative. Do not treat uncertainty
    as legal compliance.

12. Return exactly one result for every batch_id.

Allowed status values:

PASS
The document point appears consistent with the
supplied relevant provisions.

ISSUE
The document point appears to conflict with a
supplied relevant provision.

WARNING
There is a potential concern, ambiguity,
missing condition, or qualification requiring
review.

NOT VERIFIED
The supplied provisions are not sufficient to
verify the point.

BATCH ITEMS:

{json.dumps(
    batch_items,
    ensure_ascii=False,
    indent=2
)}

Return ONLY valid JSON using exactly this structure:

{{
    "results": [
        {{
            "batch_id": 1,
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
    ]
}}

Do not return Markdown.
Do not return commentary outside the JSON.
"""

    response = client.responses.create(
        model="gpt-5.6",
        input=prompt,
    )

    result_text = clean_json_response(
        response.output_text
    )

    try:
        raw_result: Any = json.loads(
            result_text
        )
    except json.JSONDecodeError as exc:
        raise ValueError(
            "The AI returned an invalid batch "
            "legal analysis JSON response."
        ) from exc

    return parse_batch_results(
        raw_result
    )


def get_batch_result_by_id(
    batch_results: list[dict[str, Any]],
    batch_id: int,
) -> dict[str, Any] | None:
    """
    Find one AI result by its batch_id.
    """

    for result in batch_results:
        raw_id: Any = result.get(
            "batch_id"
        )

        try:
            result_id = int(
                str(raw_id)
            )
        except (
            TypeError,
            ValueError,
        ):
            continue

        if result_id == batch_id:
            return result

    return None


def compare_points_with_regulations_batch(
    legal_retrieval: list[dict[str, Any]],
    batch_size: int = LEGAL_BATCH_SIZE,
) -> list[dict[str, Any]]:
    """
    Compare all retrieved document points against
    Bahrain regulations using batched OpenAI calls.

    Instead of one OpenAI request for every point,
    several points are analyzed in one request.

    Important:
    - Every point keeps its own regulations.
    - Every AI result is validated against the
      regulations supplied for that point.
    - Points with no regulations do not call AI.
    - TEST_MODE does not call OpenAI.
    - Output order follows input order.
    """

    if batch_size < 1:
        raise ValueError(
            "Legal batch size must be at least 1."
        )

    prepared_items: list[
        dict[str, Any]
    ] = []

    final_results: dict[
        int,
        dict[str, Any],
    ] = {}

    for original_index, item in enumerate(
        legal_retrieval
    ):
        raw_point: Any = item.get(
            "point",
            {},
        )

        if not isinstance(
            raw_point,
            dict,
        ):
            continue

        point = cast(
            dict[str, Any],
            raw_point,
        )

        raw_regulations_value: Any = item.get(
            "regulations",
            [],
        )

        regulations: list[
            dict[str, Any]
        ] = []

        if isinstance(
            raw_regulations_value,
            list,
        ):
            typed_regulations = cast(
                list[Any],
                raw_regulations_value,
            )

            for raw_regulation in typed_regulations:
                if not isinstance(
                    raw_regulation,
                    dict,
                ):
                    continue

                regulations.append(
                    cast(
                        dict[str, Any],
                        raw_regulation,
                    )
                )

        # No retrieved legal material:
        # no reason to spend an OpenAI request.
        if not regulations:
            final_results[
                original_index
            ] = {
                "point": point,
                "retrieved_regulations": [],
                "comparison": (
                    get_not_verified_analysis()
                ),
            }

            continue

        legal_sources = build_legal_sources(
            regulations
        )

        # TEST MODE remains deterministic.
        if settings.TEST_MODE:
            test_result = (
                get_test_legal_analysis(
                    legal_sources
                )
            )

            comparison = (
                validate_legal_analysis(
                    result=test_result,
                    legal_sources=legal_sources,
                )
            )

            final_results[
                original_index
            ] = {
                "point": point,
                "retrieved_regulations": (
                    regulations
                ),
                "comparison": comparison,
            }

            continue

        prepared_items.append(
            {
                "original_index": original_index,
                "point": point,
                "regulations": regulations,
                "legal_sources": legal_sources,
            }
        )

    # -----------------------------------------------------
    # REAL AI BATCH PROCESSING
    # -----------------------------------------------------

    if (
        not settings.TEST_MODE
        and prepared_items
    ):
        total_batches = (
            len(prepared_items)
            + batch_size
            - 1
        ) // batch_size

        for batch_number, start in enumerate(
            range(
                0,
                len(prepared_items),
                batch_size,
            ),
            start=1,
        ):
            chunk = prepared_items[
                start:start + batch_size
            ]

            print(
                f"LEGAL AI BATCH "
                f"{batch_number}/{total_batches}: "
                f"Analyzing {len(chunk)} points...",
                flush=True,
            )

            request_items: list[
                dict[str, Any]
            ] = []

            batch_lookup: dict[
                int,
                dict[str, Any],
            ] = {}

            for local_index, prepared in enumerate(
                chunk,
                start=1,
            ):
                point = cast(
                    dict[str, Any],
                    prepared["point"],
                )

                regulations = cast(
                    list[dict[str, Any]],
                    prepared["regulations"],
                )

                request_items.append(
                    build_batch_item(
                        batch_id=local_index,
                        point=point,
                        regulations=regulations,
                    )
                )

                batch_lookup[
                    local_index
                ] = prepared

            try:
                ai_batch_results = (
                    analyze_legal_batch(
                        request_items
                    )
                )

            except Exception as exc:
                # A failed batch must not leave the
                # entire document request hanging or
                # discard all other completed results.
                print(
                    f"LEGAL AI BATCH "
                    f"{batch_number}/{total_batches} "
                    f"ERROR: "
                    f"{type(exc).__name__} - {exc}",
                    flush=True,
                )

                for prepared in chunk:
                    original_index = int(
                        prepared[
                            "original_index"
                        ]
                    )

                    point = cast(
                        dict[str, Any],
                        prepared["point"],
                    )

                    regulations = cast(
                        list[dict[str, Any]],
                        prepared["regulations"],
                    )

                    final_results[
                        original_index
                    ] = {
                        "point": point,
                        "retrieved_regulations": (
                            regulations
                        ),
                        "comparison": (
                            get_not_verified_analysis(
                                (
                                    "The legal AI comparison "
                                    "could not be completed "
                                    "for this point."
                                )
                            )
                        ),
                    }

                continue

            for local_index, prepared in (
                batch_lookup.items()
            ):
                original_index = int(
                    prepared[
                        "original_index"
                    ]
                )

                point = cast(
                    dict[str, Any],
                    prepared["point"],
                )

                regulations = cast(
                    list[dict[str, Any]],
                    prepared["regulations"],
                )

                legal_sources = cast(
                    list[dict[str, Any]],
                    prepared["legal_sources"],
                )

                ai_result = (
                    get_batch_result_by_id(
                        batch_results=(
                            ai_batch_results
                        ),
                        batch_id=local_index,
                    )
                )

                if ai_result is None:
                    comparison = (
                        get_not_verified_analysis(
                            (
                                "The legal AI batch "
                                "did not return a result "
                                "for this point."
                            )
                        )
                    )

                else:
                    comparison = (
                        validate_legal_analysis(
                            result=ai_result,
                            legal_sources=(
                                legal_sources
                            ),
                        )
                    )

                final_results[
                    original_index
                ] = {
                    "point": point,
                    "retrieved_regulations": (
                        regulations
                    ),
                    "comparison": comparison,
                }

            print(
                f"LEGAL AI BATCH "
                f"{batch_number}/{total_batches} "
                "COMPLETE",
                flush=True,
            )

    # -----------------------------------------------------
    # Restore original document-point order
    # -----------------------------------------------------

    ordered_results: list[
        dict[str, Any]
    ] = []

    for original_index in range(
        len(legal_retrieval)
    ):
        result = final_results.get(
            original_index
        )

        if result is not None:
            ordered_results.append(
                result
            )

    return ordered_results