from typing import Any, TypedDict


class DraftServiceError(Exception):
    pass


class DraftType(TypedDict):
    name: str
    description: str
    required_fields: list[str]
    legal_search_queries: list[str]


DRAFT_TYPES: dict[str, DraftType] = {
    "employment_contract": {
        "name": "Employment Contract",
        "description": (
            "Create a draft employment contract "
            "for an employer and employee."
        ),
        "required_fields": [
            "employer_name",
            "employee_name",
            "job_title",
            "salary",
            "start_date",
            "contract_duration",
        ],
        "legal_search_queries": [
            "employment contract",
            "wages salary",
            "working hours",
            "annual leave",
            "termination employment",
        ],
    },

    "offer_letter": {
        "name": "Offer Letter",
        "description": (
            "Create an employment offer letter "
            "for a prospective employee."
        ),
        "required_fields": [
            "employer_name",
            "employee_name",
            "job_title",
            "salary",
            "start_date",
        ],
        "legal_search_queries": [
            "employment contract",
            "wages salary",
            "working hours",
        ],
    },

    "nda": {
        "name": "Non-Disclosure Agreement",
        "description": (
            "Create a confidentiality and "
            "non-disclosure agreement."
        ),
        "required_fields": [
            "first_party",
            "second_party",
            "purpose",
            "effective_date",
        ],
        "legal_search_queries": [
            "confidential information",
            "personal data",
            "data protection",
        ],
    },

    "warning_letter": {
        "name": "Warning Letter",
        "description": (
            "Create an employee warning letter."
        ),
        "required_fields": [
            "employer_name",
            "employee_name",
            "job_title",
            "warning_reason",
            "warning_date",
        ],
        "legal_search_queries": [
            "disciplinary sanctions",
            "employee warning",
            "termination employment",
        ],
    },

    "service_agreement": {
        "name": "Service Agreement",
        "description": (
            "Create an agreement for services "
            "between two parties."
        ),
        "required_fields": [
            "first_party",
            "second_party",
            "service_description",
            "payment_terms",
            "start_date",
        ],
        "legal_search_queries": [
            "agreement",
            "contract",
            "obligations",
        ],
    },

    "custom": {
        "name": "Custom Draft",
        "description": (
            "Create a custom legal or business draft "
            "from user-provided instructions."
        ),
        "required_fields": [
            "document_title",
            "instructions",
        ],
        "legal_search_queries": [],
    },
}


def get_draft_types() -> dict[str, DraftType]:
    return DRAFT_TYPES


def get_draft_type(
    draft_type: str,
) -> DraftType:

    normalized_type = (
        draft_type.strip().lower()
    )

    draft_config = DRAFT_TYPES.get(
        normalized_type
    )

    if draft_config is None:
        raise DraftServiceError(
            f"Unsupported draft type: {draft_type}"
        )

    return draft_config


def validate_draft_details(
    draft_type: str,
    details: dict[str, Any],
) -> dict[str, Any]:

    draft_config = get_draft_type(
        draft_type
    )

    required_fields = draft_config[
        "required_fields"
    ]

    missing_fields: list[str] = []

    for field in required_fields:
        value = details.get(field)

        if value is None:
            missing_fields.append(field)
            continue

        if (
            isinstance(value, str)
            and not value.strip()
        ):
            missing_fields.append(field)

    if missing_fields:
        raise DraftServiceError(
            "Missing required fields: "
            + ", ".join(missing_fields)
        )

    return details


def get_legal_search_queries(
    draft_type: str,
) -> list[str]:

    draft_config = get_draft_type(
        draft_type
    )

    return list(
        draft_config[
            "legal_search_queries"
        ]
    )