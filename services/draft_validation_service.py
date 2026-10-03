from typing import Any, cast


class DraftValidationError(Exception):
    pass


def build_requirement_lookup(
    legal_requirements: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:

    lookup: dict[str, dict[str, Any]] = {}

    for requirement in legal_requirements:
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

        if not law_id or not article_number:
            continue

        key = (
            law_id
            + "|"
            + article_number
        )

        lookup[key] = requirement

    return lookup


def validate_used_requirements(
    used_requirements: list[dict[str, str]],
    legal_requirements: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    trusted_lookup = build_requirement_lookup(
        legal_requirements
    )

    validated: list[dict[str, Any]] = []
    seen: set[str] = set()

    for used in used_requirements:
        law_id = str(
            used.get(
                "law_id",
                "",
            )
        ).strip()

        article_number = str(
            used.get(
                "article_number",
                "",
            )
        ).strip()

        key = (
            law_id
            + "|"
            + article_number
        )

        if key in seen:
            continue

        trusted_requirement = (
            trusted_lookup.get(key)
        )

        if trusted_requirement is None:
            continue

        seen.add(key)

        validated.append(
            dict(trusted_requirement)
        )

    return validated


def validate_generated_draft(
    ai_result: dict[str, Any],
    legal_requirements: list[dict[str, Any]],
) -> dict[str, Any]:

    title = str(
        ai_result.get(
            "title",
            "",
        )
    ).strip()

    draft = str(
        ai_result.get(
            "draft",
            "",
        )
    ).strip()

    if not title:
        raise DraftValidationError(
            "Generated draft has no title."
        )

    if not draft:
        raise DraftValidationError(
            "Generated draft has no content."
        )

    notes_raw: Any = ai_result.get(
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
            if isinstance(
                item,
                str,
            ):
                cleaned_note = item.strip()

                if cleaned_note:
                    notes.append(
                        cleaned_note
                    )

    used_raw: Any = ai_result.get(
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

            if (
                law_id
                and article_number
            ):
                used_requirements.append(
                    {
                        "law_id": law_id,
                        "article_number": (
                            article_number
                        ),
                    }
                )

    verified_sources = (
        validate_used_requirements(
            used_requirements=(
                used_requirements
            ),
            legal_requirements=(
                legal_requirements
            ),
        )
    )

    return {
        "title": title,
        "draft": draft,
        "notes": notes,
        "verified_sources": (
            verified_sources
        ),
    }