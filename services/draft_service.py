from typing import Any, TypedDict


class DraftServiceError(Exception):
    pass


class LegalTopic(TypedDict):
    key: str
    name: str
    search_queries: list[str]
    required: bool


class DraftSection(TypedDict):
    key: str
    title: str
    legal_topic: str | None


class DraftType(TypedDict):
    name: str
    description: str
    required_fields: list[str]
    legal_topics: list[LegalTopic]
    sections: list[DraftSection]


DRAFT_TYPES: dict[str, DraftType] = {

    # =========================================================
    # EMPLOYMENT CONTRACT
    # =========================================================

    "employment_contract": {
        "name": "Employment Contract",
        "description": (
            "Create a comprehensive Bahrain employment "
            "contract for an employer and employee."
        ),
        "required_fields": [
            "employer_name",
            "employee_name",
            "job_title",
            "salary",
            "start_date",
            "contract_duration",
        ],
        "legal_topics": [
            {
                "key": "employment_contract",
                "name": "Employment Contract Requirements",
                "search_queries": [
                    "employment contract",
                    "عقد العمل",
                    "عقد العمل الفردي",
                    "بيانات عقد العمل",
                ],
                "required": True,
            },
            {
                "key": "wages",
                "name": "Salary and Wages",
                "search_queries": [
                    "wages salary payment",
                    "الأجر",
                    "الأجور",
                    "أداء الأجور",
                ],
                "required": True,
            },
            {
                "key": "working_hours",
                "name": "Working Hours and Rest",
                "search_queries": [
                    "working hours rest overtime",
                    "ساعات العمل",
                    "فترات الراحة",
                    "العمل الإضافي",
                ],
                "required": True,
            },
            {
                "key": "annual_leave",
                "name": "Annual Leave",
                "search_queries": [
                    "annual leave",
                    "الإجازة السنوية",
                    "الإجازات السنوية",
                ],
                "required": True,
            },
            {
                "key": "sick_leave",
                "name": "Sick Leave",
                "search_queries": [
                    "sick leave",
                    "الإجازة المرضية",
                ],
                "required": True,
            },
            {
                "key": "probation",
                "name": "Probation",
                "search_queries": [
                    "probation period",
                    "فترة التجربة",
                    "شرط التجربة",
                ],
                "required": False,
            },
            {
                "key": "termination",
                "name": "Termination and Notice",
                "search_queries": [
                    "termination employment notice period",
                    "إنهاء عقد العمل",
                    "مهلة الإخطار",
                    "إنهاء العقد",
                ],
                "required": True,
            },
            {
                "key": "end_of_service",
                "name": "End of Service Rights",
                "search_queries": [
                    "end of service benefit",
                    "مكافأة نهاية الخدمة",
                    "مستحقات العامل",
                ],
                "required": True,
            },
            {
                "key": "confidentiality",
                "name": "Confidentiality and Personal Data",
                "search_queries": [
                    "confidentiality personal data employee",
                    "سرية البيانات",
                    "البيانات الشخصية",
                ],
                "required": False,
            },
        ],
        "sections": [
            {
                "key": "parties",
                "title": "Parties",
                "legal_topic": "employment_contract",
            },
            {
                "key": "appointment",
                "title": "Appointment and Job Duties",
                "legal_topic": "employment_contract",
            },
            {
                "key": "term",
                "title": "Term and Commencement",
                "legal_topic": "employment_contract",
            },
            {
                "key": "probation",
                "title": "Probation Period",
                "legal_topic": "probation",
            },
            {
                "key": "salary",
                "title": "Salary and Payment",
                "legal_topic": "wages",
            },
            {
                "key": "working_hours",
                "title": "Working Hours and Rest Periods",
                "legal_topic": "working_hours",
            },
            {
                "key": "annual_leave",
                "title": "Annual Leave",
                "legal_topic": "annual_leave",
            },
            {
                "key": "sick_leave",
                "title": "Sick Leave",
                "legal_topic": "sick_leave",
            },
            {
                "key": "confidentiality",
                "title": "Confidentiality and Data Protection",
                "legal_topic": "confidentiality",
            },
            {
                "key": "termination",
                "title": "Termination and Notice",
                "legal_topic": "termination",
            },
            {
                "key": "end_of_service",
                "title": "End of Service Rights",
                "legal_topic": "end_of_service",
            },
            {
                "key": "governing_law",
                "title": "Governing Law",
                "legal_topic": "employment_contract",
            },
            {
                "key": "signatures",
                "title": "Signatures",
                "legal_topic": None,
            },
        ],
    },

    # =========================================================
    # OFFER LETTER
    # =========================================================

    "offer_letter": {
        "name": "Offer Letter",
        "description": (
            "Create a Bahrain employment offer letter "
            "for a prospective employee."
        ),
        "required_fields": [
            "employer_name",
            "employee_name",
            "job_title",
            "salary",
            "start_date",
        ],
        "legal_topics": [
            {
                "key": "employment_contract",
                "name": "Employment Relationship",
                "search_queries": [
                    "employment contract",
                    "عقد العمل",
                    "بيانات عقد العمل",
                ],
                "required": True,
            },
            {
                "key": "wages",
                "name": "Salary and Wages",
                "search_queries": [
                    "wages salary",
                    "الأجر",
                    "الأجور",
                ],
                "required": True,
            },
            {
                "key": "working_hours",
                "name": "Working Hours",
                "search_queries": [
                    "working hours",
                    "ساعات العمل",
                ],
                "required": False,
            },
            {
                "key": "probation",
                "name": "Probation",
                "search_queries": [
                    "probation period",
                    "فترة التجربة",
                ],
                "required": False,
            },
        ],
        "sections": [
            {
                "key": "offer",
                "title": "Offer of Employment",
                "legal_topic": "employment_contract",
            },
            {
                "key": "position",
                "title": "Position",
                "legal_topic": "employment_contract",
            },
            {
                "key": "salary",
                "title": "Salary",
                "legal_topic": "wages",
            },
            {
                "key": "start_date",
                "title": "Start Date",
                "legal_topic": "employment_contract",
            },
            {
                "key": "working_hours",
                "title": "Working Hours",
                "legal_topic": "working_hours",
            },
            {
                "key": "probation",
                "title": "Probation",
                "legal_topic": "probation",
            },
            {
                "key": "acceptance",
                "title": "Acceptance",
                "legal_topic": None,
            },
        ],
    },

    # =========================================================
    # NDA
    # =========================================================

    "nda": {
        "name": "Non-Disclosure Agreement",
        "description": (
            "Create a confidentiality and non-disclosure "
            "agreement with Bahrain legal grounding."
        ),
        "required_fields": [
            "first_party",
            "second_party",
            "purpose",
            "effective_date",
        ],
        "legal_topics": [
            {
                "key": "confidentiality",
                "name": "Confidentiality",
                "search_queries": [
                    "confidential information confidentiality",
                    "سرية المعلومات",
                    "عدم الإفصاح",
                ],
                "required": True,
            },
            {
                "key": "personal_data",
                "name": "Personal Data",
                "search_queries": [
                    "personal data protection",
                    "البيانات الشخصية",
                    "حماية البيانات الشخصية",
                ],
                "required": False,
            },
            {
                "key": "data_security",
                "name": "Data Security and Confidentiality",
                "search_queries": [
                    "data security confidentiality processing",
                    "سرية المعالجة",
                    "التدابير الفنية والتنظيمية",
                ],
                "required": False,
            },
            {
                "key": "data_transfer",
                "name": "Transfer of Personal Data",
                "search_queries": [
                    "international data transfer",
                    "نقل البيانات الشخصية",
                ],
                "required": False,
            },
        ],
        "sections": [
            {
                "key": "parties",
                "title": "Parties",
                "legal_topic": None,
            },
            {
                "key": "purpose",
                "title": "Purpose",
                "legal_topic": "confidentiality",
            },
            {
                "key": "definition",
                "title": "Confidential Information",
                "legal_topic": "confidentiality",
            },
            {
                "key": "obligations",
                "title": "Confidentiality Obligations",
                "legal_topic": "confidentiality",
            },
            {
                "key": "personal_data",
                "title": "Personal Data Protection",
                "legal_topic": "personal_data",
            },
            {
                "key": "exceptions",
                "title": "Exclusions",
                "legal_topic": None,
            },
            {
                "key": "term",
                "title": "Term",
                "legal_topic": None,
            },
            {
                "key": "return_information",
                "title": "Return or Destruction of Information",
                "legal_topic": "confidentiality",
            },
            {
                "key": "governing_law",
                "title": "Governing Law",
                "legal_topic": None,
            },
            {
                "key": "signatures",
                "title": "Signatures",
                "legal_topic": None,
            },
        ],
    },

    # =========================================================
    # WARNING LETTER
    # =========================================================

    "warning_letter": {
        "name": "Warning Letter",
        "description": (
            "Create an employee warning letter with "
            "relevant Bahrain labour-law grounding."
        ),
        "required_fields": [
            "employer_name",
            "employee_name",
            "job_title",
            "warning_reason",
            "warning_date",
        ],
        "legal_topics": [
            {
                "key": "disciplinary",
                "name": "Disciplinary Rules",
                "search_queries": [
                    "disciplinary sanctions employee warning",
                    "الجزاءات التأديبية",
                    "إنذار العامل",
                ],
                "required": True,
            },
            {
                "key": "termination",
                "name": "Termination",
                "search_queries": [
                    "termination dismissal misconduct",
                    "فصل العامل",
                    "إنهاء عقد العمل",
                ],
                "required": False,
            },
        ],
        "sections": [
            {
                "key": "employee",
                "title": "Employee Details",
                "legal_topic": None,
            },
            {
                "key": "incident",
                "title": "Reason for Warning",
                "legal_topic": "disciplinary",
            },
            {
                "key": "required_action",
                "title": "Required Corrective Action",
                "legal_topic": "disciplinary",
            },
            {
                "key": "consequences",
                "title": "Consequences of Further Violations",
                "legal_topic": "termination",
            },
            {
                "key": "acknowledgement",
                "title": "Acknowledgement",
                "legal_topic": None,
            },
        ],
    },

    # =========================================================
    # SERVICE AGREEMENT
    # =========================================================

    "service_agreement": {
        "name": "Service Agreement",
        "description": (
            "Create a structured services agreement "
            "between two parties."
        ),
        "required_fields": [
            "first_party",
            "second_party",
            "service_description",
            "payment_terms",
            "start_date",
        ],
        "legal_topics": [
            {
                "key": "contract",
                "name": "Contract",
                "search_queries": [
                    "contract agreement",
                    "عقد اتفاق",
                ],
                "required": True,
            },
            {
                "key": "obligations",
                "name": "Contractual Obligations",
                "search_queries": [
                    "contract obligations",
                    "التزامات العقد",
                    "الالتزامات التعاقدية",
                ],
                "required": True,
            },
            {
                "key": "confidentiality",
                "name": "Confidentiality",
                "search_queries": [
                    "confidentiality",
                    "سرية المعلومات",
                ],
                "required": False,
            },
            {
                "key": "personal_data",
                "name": "Personal Data",
                "search_queries": [
                    "personal data",
                    "حماية البيانات الشخصية",
                ],
                "required": False,
            },
        ],
        "sections": [
            {
                "key": "parties",
                "title": "Parties",
                "legal_topic": "contract",
            },
            {
                "key": "services",
                "title": "Scope of Services",
                "legal_topic": "obligations",
            },
            {
                "key": "payment",
                "title": "Fees and Payment",
                "legal_topic": "contract",
            },
            {
                "key": "responsibilities",
                "title": "Responsibilities of the Parties",
                "legal_topic": "obligations",
            },
            {
                "key": "confidentiality",
                "title": "Confidentiality",
                "legal_topic": "confidentiality",
            },
            {
                "key": "data_protection",
                "title": "Data Protection",
                "legal_topic": "personal_data",
            },
            {
                "key": "termination",
                "title": "Termination",
                "legal_topic": "contract",
            },
            {
                "key": "governing_law",
                "title": "Governing Law",
                "legal_topic": "contract",
            },
            {
                "key": "signatures",
                "title": "Signatures",
                "legal_topic": None,
            },
        ],
    },

    # =========================================================
    # CUSTOM
    # =========================================================

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
        "legal_topics": [],
        "sections": [],
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

        value = details.get(
            field
        )

        if value is None:
            missing_fields.append(
                field
            )
            continue

        if (
            isinstance(value, str)
            and not value.strip()
        ):
            missing_fields.append(
                field
            )

    if missing_fields:
        raise DraftServiceError(
            "Missing required fields: "
            + ", ".join(
                missing_fields
            )
        )

    return details


def get_legal_topics(
    draft_type: str,
) -> list[LegalTopic]:
    """
    Return structured legal topics for
    the selected draft type.
    """

    draft_config = get_draft_type(
        draft_type
    )

    return list(
        draft_config[
            "legal_topics"
        ]
    )


def get_draft_sections(
    draft_type: str,
) -> list[DraftSection]:
    """
    Return the expected professional
    structure for the draft.
    """

    draft_config = get_draft_type(
        draft_type
    )

    return list(
        draft_config[
            "sections"
        ]
    )


def get_legal_search_queries(
    draft_type: str,
) -> list[str]:
    """
    Backward-compatible function.

    Converts the new structured legal topics
    into a flat query list so existing services
    continue working while we upgrade them.
    """

    legal_topics = get_legal_topics(
        draft_type
    )

    queries: list[str] = []

    for topic in legal_topics:

        for query in topic[
            "search_queries"
        ]:

            if query not in queries:
                queries.append(
                    query
                )

    return queries