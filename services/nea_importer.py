import json
import re
import urllib.request
from pathlib import Path
from typing import Any, cast

import pymupdf


BASE_DIR = Path(__file__).resolve().parent.parent

NEA_DIR = (
    BASE_DIR
    / "knowledge"
    / "bahrain"
    / "nea"
)

SOURCES_FILE = (
    NEA_DIR
    / "sources"
    / "sources.json"
)

KNOWLEDGE_FILE = (
    NEA_DIR
    / "standards.json"
)


class NEAImporterError(Exception):
    pass


def load_nea_sources() -> list[dict[str, Any]]:
    if not SOURCES_FILE.exists():
        raise NEAImporterError(
            "NEA sources file was not found."
        )

    try:
        with open(
            SOURCES_FILE,
            "r",
            encoding="utf-8",
        ) as file:
            raw_data: Any = json.load(file)

    except Exception as exc:
        raise NEAImporterError(
            "Could not read NEA sources file."
        ) from exc

    if not isinstance(raw_data, dict):
        raise NEAImporterError(
            "Invalid NEA sources file."
        )

    data = cast(
        dict[str, Any],
        raw_data,
    )

    raw_sources: Any = data.get(
        "sources",
        [],
    )

    if not isinstance(raw_sources, list):
        raise NEAImporterError(
            "Invalid NEA sources list."
        )

    sources: list[dict[str, Any]] = []

    for raw_source in cast(
        list[Any],
        raw_sources,
    ):
        if not isinstance(
            raw_source,
            dict,
        ):
            continue

        source = cast(
            dict[str, Any],
            raw_source,
        )

        if not source.get(
            "enabled",
            False,
        ):
            continue

        if not source.get(
            "verified",
            False,
        ):
            continue

        sources.append(
            source
        )

    return sources


def download_nea_document(
    document_url: str,
) -> bytes:
    try:
        request = urllib.request.Request(
            document_url,
            headers={
                "User-Agent": "Mozilla/5.0",
            },
        )

        with urllib.request.urlopen(
            request,
            timeout=30,
        ) as response:
            content = response.read()

        if not content:
            raise NEAImporterError(
                "Downloaded NEA document is empty."
            )

        return content

    except NEAImporterError:
        raise

    except Exception as exc:
        raise NEAImporterError(
            "Could not download NEA document."
        ) from exc


def extract_pdf_text(
    content: bytes,
) -> str:
    try:
        document = pymupdf.open(
            stream=content,
            filetype="pdf",
        )

        pages: list[str] = []

        for page_number in range(
            len(document)
        ):
            page: Any = cast(
                Any,
                document[page_number],
            )

            text: str = page.get_text(
                "text"
            )

            if text.strip():
                pages.append(
                    text.strip()
                )

        document.close()

        extracted_text = "\n\n".join(
            pages
        )

        if not extracted_text.strip():
            raise NEAImporterError(
                "No readable text was found "
                "in the NEA PDF."
            )

        return extracted_text

    except NEAImporterError:
        raise

    except Exception as exc:
        raise NEAImporterError(
            "Could not extract text "
            "from NEA PDF."
        ) from exc


def clean_nea_text(
    text: str,
) -> str:
    text = re.sub(
        r"Website standards\s+Page\s*\|\s*\d+",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"\r\n?",
        "\n",
        text,
    )

    text = re.sub(
        r"[ \t]+",
        " ",
        text,
    )

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text,
    )

    return text.strip()


def parse_nea_sections(
    text: str,
    source: dict[str, Any],
) -> list[dict[str, Any]]:
    cleaned_text = clean_nea_text(
        text
    )

    lines = cleaned_text.splitlines()

    section_pattern = re.compile(
        r"^\s*(\d+\.\d+(?:\.\d+)*)\s+(.+?)\s*$"
    )

    contents_line_pattern = re.compile(
        r"\.{3,}\s*\d+\s*$"
    )

    standards: list[dict[str, Any]] = []

    current_number: str | None = None
    current_title: str | None = None
    current_lines: list[str] = []

    started_real_content = False

    def save_current_section() -> None:
        if (
            current_number is None
            or current_title is None
        ):
            return

        body = "\n".join(
            current_lines
        ).strip()

        if not body:
            return

        standards.append(
            {
                "source_id": source.get(
                    "source_id"
                ),
                "source_title": source.get(
                    "title"
                ),
                "category": source.get(
                    "category"
                ),
                "authority": source.get(
                    "authority"
                ),
                "section_number": current_number,
                "title": current_title,
                "text": body,
                "source_page_url": source.get(
                    "source_page_url"
                ),
                "document_url": source.get(
                    "document_url"
                ),
            }
        )

    for raw_line in lines:
        line = raw_line.strip()

        if not line:
            continue

        match = section_pattern.match(
            line
        )

        if match:
            section_number = match.group(1)
            section_title = match.group(2).strip()

            # Ignore entries from the table of contents.
            if contents_line_pattern.search(
                section_title
            ):
                continue

            # The actual document body starts at 1.0 Introduction.
            if (
                section_number == "1.0"
                and section_title.lower().startswith(
                    "introduction"
                )
            ):
                started_real_content = True

            if not started_real_content:
                continue

            save_current_section()

            current_number = section_number
            current_title = section_title
            current_lines = []

            continue

        if (
            started_real_content
            and current_number is not None
        ):
            current_lines.append(
                line
            )

    save_current_section()

    return standards


def build_nea_knowledge_base() -> list[dict[str, Any]]:
    sources = load_nea_sources()

    if not sources:
        raise NEAImporterError(
            "No enabled and verified "
            "NEA sources were found."
        )

    all_standards: list[dict[str, Any]] = []

    for source in sources:
        document_url = str(
            source.get(
                "document_url",
                "",
            )
        ).strip()

        if not document_url:
            continue

        content = download_nea_document(
            document_url
        )

        text = extract_pdf_text(
            content
        )

        standards = parse_nea_sections(
            text=text,
            source=source,
        )

        all_standards.extend(
            standards
        )

    if not all_standards:
        raise NEAImporterError(
            "No NEA standards could be parsed."
        )

    save_nea_standards(
        all_standards
    )

    return all_standards


def save_nea_standards(
    standards: list[dict[str, Any]],
) -> None:
    NEA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    data = {
        "standards": standards,
    }

    with open(
        KNOWLEDGE_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2,
        )