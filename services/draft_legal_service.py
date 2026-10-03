from typing import Any

from services.draft_service import (
    get_legal_search_queries,
)
from services.legal_retriever import (
    search_regulations,
)


class DraftLegalServiceError(Exception):
    pass


def retrieve_draft_legal_requirements(
    draft_type: str,
    limit_per_query: int = 3,
) -> list[dict[str, Any]]:
    """
    Retrieve relevant Bahrain legal provisions
    for the selected draft type.
    """

    search_queries = get_legal_search_queries(
        draft_type
    )

    if not search_queries:
        return []

    retrieved_requirements: list[
        dict[str, Any]
    ] = []

    seen_requirements: set[str] = set()

    for query in search_queries:
        try:
            matches = search_regulations(
                query=query,
                limit=limit_per_query,
            )

        except Exception as exc:
            raise DraftLegalServiceError(
                "Could not retrieve legal "
                f"requirements for: {query}"
            ) from exc

        for match in matches:
            law_id = str(
                match.get(
                    "law_id",
                    "",
                )
            )

            article_number = str(
                match.get(
                    "article_number",
                    "",
                )
            )

            title = str(
                match.get(
                    "title",
                    "",
                )
            )

            unique_key = (
                law_id
                + "|"
                + article_number
                + "|"
                + title
            )

            if unique_key in seen_requirements:
                continue

            seen_requirements.add(
                unique_key
            )

            requirement = dict(match)

            requirement[
                "matched_query"
            ] = query

            retrieved_requirements.append(
                requirement
            )

    return retrieved_requirements