import json
import re
from pathlib import Path
from typing import Any, cast


REGULATIONS_FILE = (
    Path(__file__).resolve().parent.parent
    / "knowledge"
    / "bahrain"
    / "regulations.json"
)


# Common words that are not very useful
# when searching Bahrain regulations.
STOP_WORDS = {
    "في",
    "من",
    "على",
    "إلى",
    "الى",
    "عن",
    "أن",
    "ان",
    "إن",
    "هذا",
    "هذه",
    "ذلك",
    "تلك",
    "بين",
    "أو",
    "او",
    "و",
    "ثم",
    "مع",
    "كل",
    "أي",
    "اي",
    "هو",
    "هي",
    "كان",
    "تكون",
    "يكون",
    "تم",
    "يتم",
    "قد",
    "ما",
    "لا",
}


def load_regulations() -> list[dict[str, Any]]:
    """
    Load Bahrain regulations from
    the local knowledge base.
    """

    if not REGULATIONS_FILE.exists():
        raise FileNotFoundError(
            "Bahrain regulations knowledge base "
            "was not found."
        )

    with open(
        REGULATIONS_FILE,
        "r",
        encoding="utf-8"
    ) as file:
        raw_data: Any = json.load(file)

    if not isinstance(raw_data, dict):
        raise ValueError(
            "Invalid regulations knowledge base."
        )

    data = cast(
        dict[str, Any],
        raw_data
    )

    raw_regulations: Any = data.get(
        "regulations",
        []
    )

    if not isinstance(
        raw_regulations,
        list
    ):
        return []

    regulations = cast(
        list[dict[str, Any]],
        raw_regulations
    )

    return regulations


def normalize_text(
    text: str
) -> str:
    """
    Normalize Arabic and English text
    to improve legal matching.
    """

    text = text.lower()

    # Normalize Arabic letters.
    text = re.sub(
        r"[أإآٱ]",
        "ا",
        text
    )

    text = text.replace(
        "ى",
        "ي"
    )

    text = text.replace(
        "ة",
        "ه"
    )

    text = text.replace(
        "ؤ",
        "و"
    )

    text = text.replace(
        "ئ",
        "ي"
    )

    # Remove Arabic tatweel.
    text = text.replace(
        "ـ",
        ""
    )

    # Remove Arabic diacritics.
    text = re.sub(
        r"[\u064B-\u065F\u0670]",
        "",
        text
    )

    # Remove punctuation.
    text = re.sub(
        r"[^\w\s]",
        " ",
        text
    )

    # Remove extra spaces.
    text = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    return text


def get_query_words(
    query: str
) -> list[str]:
    """
    Extract useful and unique
    search words from a query.
    """

    normalized_query = normalize_text(
        query
    )

    words = normalized_query.split()

    normalized_stop_words = {
        normalize_text(word)
        for word in STOP_WORDS
    }

    useful_words: list[str] = []

    for word in words:

        if word in normalized_stop_words:
            continue

        if len(word) <= 1:
            continue

        if word not in useful_words:
            useful_words.append(
                word
            )

    return useful_words


def get_query_phrases(
    query: str
) -> list[str]:
    """
    Create useful two-word and
    three-word phrases from a query.
    """

    words = get_query_words(
        query
    )

    phrases: list[str] = []

    # Two-word phrases.
    for index in range(
        len(words) - 1
    ):

        phrase = (
            f"{words[index]} "
            f"{words[index + 1]}"
        )

        phrases.append(
            phrase
        )

    # Three-word phrases.
    for index in range(
        len(words) - 2
    ):

        phrase = (
            f"{words[index]} "
            f"{words[index + 1]} "
            f"{words[index + 2]}"
        )

        phrases.append(
            phrase
        )

    return phrases


def count_word_matches(
    query_words: list[str],
    regulation_text: str
) -> int:
    """
    Count how many unique query
    words appear in a regulation.
    """

    matches = 0

    for word in query_words:

        if word in regulation_text:
            matches += 1

    return matches


def calculate_score(
    query: str,
    regulation: dict[str, Any]
) -> int:
    """
    Calculate relevance between
    a query and one regulation.

    Phrase matches and concept
    coverage receive more weight
    than isolated word matches.
    """

    query_normalized = normalize_text(
        query
    )

    query_words = get_query_words(
        query
    )

    query_phrases = get_query_phrases(
        query
    )

    title = normalize_text(
        str(
            regulation.get(
                "title",
                ""
            )
        )
    )

    regulation_text = normalize_text(
        str(
            regulation.get(
                "text",
                ""
            )
        )
    )

    category = normalize_text(
        str(
            regulation.get(
                "category",
                ""
            )
        )
    )

    searchable_text = (
        f"{title} "
        f"{category} "
        f"{regulation_text}"
    )

    score = 0

    # Very strong match:
    # the complete query exists
    # inside the article.
    if (
        query_normalized
        and query_normalized
        in regulation_text
    ):
        score += 25

    # Phrase matching.
    for phrase in query_phrases:

        word_count = len(
            phrase.split()
        )

        if phrase in regulation_text:

            if word_count >= 3:
                score += 12

            else:
                score += 7

    # Individual word matching.
    for word in query_words:

        if word in regulation_text:
            score += 3

        if word in title:
            score += 1

        if word in category:
            score += 2

    matched_words = count_word_matches(
        query_words=query_words,
        regulation_text=searchable_text,
    )

    total_words = len(
        query_words
    )

    # Coverage bonus:
    # reward articles that match
    # several concepts in the query.
    if total_words > 0:

        coverage = (
            matched_words
            / total_words
        )

        if coverage == 1:
            score += 15

        elif coverage >= 0.75:
            score += 10

        elif coverage >= 0.50:
            score += 5

    # Ignore articles with no
    # meaningful matching words.
    if matched_words == 0:
        return 0

    return score


def search_regulations(
    query: str,
    limit: int = 5
) -> list[dict[str, Any]]:
    """
    Search Bahrain regulations
    and return the most relevant
    legal provisions.
    """

    if not query.strip():
        return []

    regulations = load_regulations()

    results: list[
        dict[str, Any]
    ] = []

    for regulation in regulations:

        score = calculate_score(
            query=query,
            regulation=regulation,
        )

        if score <= 0:
            continue

        result: dict[str, Any] = (
            regulation.copy()
        )

        result[
            "relevance_score"
        ] = score

        results.append(
            result
        )

    results.sort(
        key=lambda item: int(
            item.get(
                "relevance_score",
                0
            )
        ),
        reverse=True,
    )

    return results[
        :limit
    ]