import json
import re
from io import BytesIO
from pathlib import Path
from typing import Any, cast

import requests
from docx import Document


BASE_DIR = Path(__file__).resolve().parent.parent

REGULATIONS_FILE = (
    BASE_DIR
    / "knowledge"
    / "bahrain"
    / "regulations.json"
)

SOURCES_FILE = (
    BASE_DIR
    / "knowledge"
    / "bahrain"
    / "sources"
    / "sources.json"
)


def load_json_file(
    file_path: Path
) -> dict[str, Any]:
    """
    Load and validate a JSON object.
    """

    if not file_path.exists():
        raise FileNotFoundError(
            f"{file_path.name} was not found."
        )

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:
        raw_data: Any = json.load(file)

    if not isinstance(raw_data, dict):
        raise ValueError(
            f"Invalid format in {file_path.name}."
        )

    return cast(
        dict[str, Any],
        raw_data
    )


def load_knowledge_base() -> dict[str, Any]:
    """
    Load the Bahrain regulations knowledge base.
    """

    return load_json_file(
        REGULATIONS_FILE
    )


def load_sources() -> list[dict[str, Any]]:
    """
    Load enabled and verified legislation sources.
    """

    data = load_json_file(
        SOURCES_FILE
    )

    raw_sources = data.get(
        "sources",
        []
    )

    if not isinstance(raw_sources, list):
        raise ValueError(
            "The sources field must be a list."
        )

    typed_sources = cast(
        list[Any],
        raw_sources
    )

    sources: list[dict[str, Any]] = []

    for item in typed_sources:

        if not isinstance(item, dict):
            continue

        source = cast(
            dict[str, Any],
            item
        )

        if source.get("enabled") is not True:
            continue

        if source.get("verified") is not True:
            continue

        sources.append(
            source
        )

    return sources


def get_source_by_id(
    source_id: str
) -> dict[str, Any]:
    """
    Find one enabled and verified source.
    """

    sources = load_sources()

    for source in sources:

        current_id = str(
            source.get(
                "id",
                ""
            )
        ).strip()

        if current_id == source_id:
            return source

    raise ValueError(
        f"Source '{source_id}' was not found "
        "or is not enabled and verified."
    )


def save_knowledge_base(
    data: dict[str, Any]
) -> None:
    """
    Save the Bahrain regulations knowledge base.
    """

    with open(
        REGULATIONS_FILE,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2,
        )


def download_official_docx(
    url: str
) -> bytes:
    """
    Download an official legislation DOCX.
    """

    if not url:
        raise ValueError(
            "The consolidated source URL is missing."
        )

    headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/151.0.0.0 Safari/537.36"
        )
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    return response.content


def extract_docx_text(
    docx_content: bytes
) -> str:
    """
    Extract clean text from a DOCX.
    """

    document = Document(
        BytesIO(docx_content)
    )

    paragraphs: list[str] = []

    for paragraph in document.paragraphs:

        text = paragraph.text.strip()

        if text:
            paragraphs.append(
                text
            )

    return "\n".join(
        paragraphs
    )


def get_main_law_text(
    text: str,
    marker: str
) -> str:
    """
    Find the main law text using its configured
    title marker.

    LLOC consolidated documents can contain the
    title once in the promulgating section and
    again before the main law text.
    """

    if not marker:
        raise ValueError(
            "law_title_marker is missing."
        )

    first_position = text.find(
        marker
    )

    if first_position == -1:
        raise ValueError(
            f"Law title marker was not found: {marker}"
        )

    second_position = text.find(
        marker,
        first_position + len(marker)
    )

    if second_position != -1:
        return text[
            second_position:
        ]

    return text[
        first_position:
    ]


def split_articles(
    text: str
) -> list[dict[str, str]]:
    """
    Split Arabic legislation into articles.

    Supports examples such as:
    المادة (1)
    المادة (2)
    المادة (2) مكرراً

    مادة (1)
    مادة (2)
    مادة (2) مكرراً
    """

    pattern = re.compile(
        r"(?m)^(?:المادة|مادة)\s*"
        r"[\(\（]?\s*(\d+)\s*[\)\）]?"
        r"(?:\s+(مكرراً(?:\s+\d+)?))?"
        r"\s*$"
    )

    matches = list(
        pattern.finditer(text)
    )

    articles: list[
        dict[str, str]
    ] = []

    for index, match in enumerate(
        matches
    ):

        number = match.group(1)
        repeated = match.group(2)

        if repeated:
            article_name = (
                f"{number} {repeated}"
            )
        else:
            article_name = number

        start = match.end()

        if index + 1 < len(matches):
            end = matches[
                index + 1
            ].start()
        else:
            end = len(text)

        article_text = text[
            start:end
        ].strip()

        if not article_text:
            continue

        articles.append(
            {
                "article": article_name,
                "text": article_text,
            }
        )

    return articles


def make_article_id(
    source_id: str,
    article: str
) -> str:
    """
    Create a unique ID for an article.
    """

    clean_article = (
        article
        .replace(
            "مكرراً",
            "BIS"
        )
        .replace(
            " ",
            "-"
        )
    )

    return (
        f"{source_id}-"
        f"ARTICLE-{clean_article}"
    )


def get_existing_regulations(
    data: dict[str, Any]
) -> list[dict[str, Any]]:
    """
    Read existing regulations safely.
    """

    raw_regulations = data.get(
        "regulations",
        []
    )

    if not isinstance(
        raw_regulations,
        list
    ):
        return []

    typed_regulations = cast(
        list[Any],
        raw_regulations
    )

    regulations: list[
        dict[str, Any]
    ] = []

    for item in typed_regulations:

        if isinstance(item, dict):

            regulation = cast(
                dict[str, Any],
                item
            )

            regulations.append(
                regulation
            )

    return regulations


def upsert_regulations(
    existing_regulations: list[
        dict[str, Any]
    ],
    new_regulations: list[
        dict[str, Any]
    ],
) -> list[dict[str, Any]]:
    """
    Add new regulations and update matching IDs
    without deleting regulations from other laws.
    """

    regulations_by_id: dict[
        str,
        dict[str, Any]
    ] = {}

    for regulation in existing_regulations:

        regulation_id = str(
            regulation.get(
                "id",
                ""
            )
        ).strip()

        if regulation_id:

            regulations_by_id[
                regulation_id
            ] = regulation

    for regulation in new_regulations:

        regulation_id = str(
            regulation.get(
                "id",
                ""
            )
        ).strip()

        if not regulation_id:
            continue

        regulations_by_id[
            regulation_id
        ] = regulation

    return list(
        regulations_by_id.values()
    )


def import_source(
    source_id: str
) -> int:
    """
    Import one configured legislation source
    from sources.json.
    """

    source = get_source_by_id(
        source_id
    )

    source_format = str(
        source.get(
            "source_format",
            ""
        )
    ).strip().lower()

    parser_type = str(
        source.get(
            "parser_type",
            ""
        )
    ).strip()

    if source_format != "docx":
        raise ValueError(
            f"Unsupported source format: "
            f"{source_format}"
        )

    if (
        parser_type
        != "bahrain_lloc_consolidated_docx"
    ):
        raise ValueError(
            f"Unsupported parser type: "
            f"{parser_type}"
        )

    consolidated_url = str(
        source.get(
            "consolidated_url",
            ""
        )
    ).strip()

    law_title_marker = str(
        source.get(
            "law_title_marker",
            ""
        )
    ).strip()

    title = str(
        source.get(
            "title_ar",
            ""
        )
    ).strip()

    law_number = str(
        source.get(
            "law_number",
            ""
        )
    ).strip()

    category = str(
        source.get(
            "category",
            ""
        )
    ).strip()

    source_page_url = str(
        source.get(
            "source_page_url",
            ""
        )
    ).strip()

    raw_year = source.get(
        "year",
        0
    )

    if not isinstance(raw_year, int):
        raise ValueError(
            "Source year must be an integer."
        )

    print(
        f"Downloading source: {source_id}"
    )

    docx_content = download_official_docx(
        consolidated_url
    )

    print(
        "Extracting text..."
    )

    full_text = extract_docx_text(
        docx_content
    )

    main_law_text = get_main_law_text(
        text=full_text,
        marker=law_title_marker,
    )

    print(
        "Splitting articles..."
    )

    articles = split_articles(
        main_law_text
    )

    if not articles:
        raise ValueError(
            "No articles were detected."
        )

    new_regulations: list[
        dict[str, Any]
    ] = []

    for article in articles:

        article_name = article[
            "article"
        ]

        regulation: dict[
            str,
            Any
        ] = {
            "id": make_article_id(
                source_id=source_id,
                article=article_name,
            ),
            "source_id": source_id,
            "title": title,
            "law_number": law_number,
            "year": raw_year,
            "category": category,
            "article": article_name,
            "text": article["text"],
            "source_url": (
                source_page_url
                or consolidated_url
            ),
            "consolidated_url": (
                consolidated_url
            ),
            "source_type": "official",
            "effective_status": (
                "consolidated_source"
            ),
            "notes": (
                "Imported from a configured "
                "official legislation source."
            ),
        }

        new_regulations.append(
            regulation
        )

    data = load_knowledge_base()

    existing_regulations = (
        get_existing_regulations(
            data
        )
    )

    data["regulations"] = (
        upsert_regulations(
            existing_regulations=
                existing_regulations,
            new_regulations=
                new_regulations,
        )
    )

    save_knowledge_base(
        data
    )

    return len(
        new_regulations
    )


def import_labour_law() -> int:
    """
    Backwards-compatible function used by
    import_labour_law.py.
    """

    return import_source(
        "BH-LABOUR-36-2012"
    )