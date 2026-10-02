import json
import re
from pathlib import Path
from typing import Any, cast


BASE_DIR = Path(__file__).resolve().parent.parent

NEA_KNOWLEDGE_FILE = (
    BASE_DIR
    / "knowledge"
    / "bahrain"
    / "nea"
    / "standards.json"
)


class NEARetrieverError(Exception):
    pass


def load_nea_standards() -> list[dict[str, Any]]:
    if not NEA_KNOWLEDGE_FILE.exists():
        raise NEARetrieverError(
            "NEA knowledge base was not found."
        )

    try:
        with open(
            NEA_KNOWLEDGE_FILE,
            "r",
            encoding="utf-8",
        ) as file:
            raw_data: Any = json.load(file)

    except Exception as exc:
        raise NEARetrieverError(
            "Could not read NEA knowledge base."
        ) from exc

    if not isinstance(raw_data, dict):
        raise NEARetrieverError(
            "Invalid NEA knowledge base."
        )

    data = cast(
        dict[str, Any],
        raw_data,
    )

    raw_standards: Any = data.get(
        "standards",
        [],
    )

    if not isinstance(
        raw_standards,
        list,
    ):
        raise NEARetrieverError(
            "Invalid NEA standards list."
        )

    standards: list[dict[str, Any]] = []

    for raw_standard in cast(
        list[Any],
        raw_standards,
    ):
        if isinstance(
            raw_standard,
            dict,
        ):
            standards.append(
                cast(
                    dict[str, Any],
                    raw_standard,
                )
            )

    return standards


def normalize_text(
    text: str,
) -> str:
    text = text.lower()

    text = re.sub(
        r"[^a-z0-9\s]",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def tokenize(
    text: str,
) -> set[str]:
    normalized = normalize_text(
        text
    )

    words = normalized.split()

    stop_words = {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "in",
        "is",
        "it",
        "of",
        "on",
        "or",
        "that",
        "the",
        "this",
        "to",
        "use",
        "with",
    }

    return {
        word
        for word in words
        if len(word) > 1
        and word not in stop_words
    }


def calculate_relevance_score(
    query: str,
    standard: dict[str, Any],
) -> float:
    query_tokens = tokenize(
        query
    )

    if not query_tokens:
        return 0.0

    title = str(
        standard.get(
            "title",
            "",
        )
    )

    body = str(
        standard.get(
            "text",
            "",
        )
    )

    title_tokens = tokenize(
        title
    )

    body_tokens = tokenize(
        body
    )

    title_matches = len(
        query_tokens.intersection(
            title_tokens
        )
    )

    body_matches = len(
        query_tokens.intersection(
            body_tokens
        )
    )

    # Title matches are much more important
    # than matches found only in the body.
    score = (
        title_matches * 10.0
        + body_matches * 1.0
    )

    normalized_title = normalize_text(
        title
    )

    normalized_query = normalize_text(
        query
    )

    # Exact query phrase appears in the title.
    if (
        normalized_query
        and normalized_query
        in normalized_title
    ):
        score += 10.0

    # Exact title match gets the strongest boost.
    if (
        normalized_query
        and normalized_query
        == normalized_title
    ):
        score += 10.0

    return score


def search_nea_standards(
    query: str,
    limit: int = 5,
    minimum_score: float = 5.0,
) -> list[dict[str, Any]]:
    if not query.strip():
        return []

    standards = load_nea_standards()

    scored_results: list[
        tuple[float, dict[str, Any]]
    ] = []

    for standard in standards:
        score = calculate_relevance_score(
            query=query,
            standard=standard,
        )

        # Ignore weak matches found only
        # incidentally in the section body.
        if score < minimum_score:
            continue

        scored_results.append(
            (
                score,
                standard,
            )
        )

    scored_results.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    results: list[dict[str, Any]] = []

    for score, standard in scored_results[
        :limit
    ]:
        result = dict(
            standard
        )

        result[
            "relevance_score"
        ] = score

        results.append(
            result
        )

    return results


def retrieve_design_requirements(
    detected_elements: list[str],
    limit_per_element: int = 3,
) -> list[dict[str, Any]]:
    retrieved: list[
        dict[str, Any]
    ] = []

    seen_sections: set[str] = set()

    for element in detected_elements:
        matches = search_nea_standards(
            query=element,
            limit=limit_per_element,
            minimum_score=5.0,
        )

        for match in matches:
            section_number = str(
                match.get(
                    "section_number",
                    "",
                )
            )

            unique_key = (
                section_number
                + "|"
                + str(
                    match.get(
                        "title",
                        "",
                    )
                )
            )

            if unique_key in seen_sections:
                continue

            seen_sections.add(
                unique_key
            )

            result = dict(
                match
            )

            result[
                "matched_element"
            ] = element

            retrieved.append(
                result
            )

    return retrieved