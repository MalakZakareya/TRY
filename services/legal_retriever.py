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
    "the",
    "a",
    "an",
    "of",
    "for",
    "to",
    "in",
    "and",
    "or",
    "with",
}


# -------------------------------------------------
# Bilingual Bahrain legal concept map
# -------------------------------------------------

LEGAL_CONCEPTS: dict[str, list[str]] = {

    "employment_contract": [
        "employment contract",
        "work contract",
        "labour contract",
        "labor contract",
        "employment agreement",
        "employment contract requirements",
        "employment contract details",
        "employment contract terms",
        "written employment contract",
        "عقد العمل",
        "عقد عمل",
        "عقد العمل الفردي",
        "بيانات عقد العمل",
        "البيانات الجوهرية",
        "البيانات الجوهرية لعقد العمل",
        "تحرير عقد العمل",
        "عقد العمل ثابتاً بالكتابة",
        "عقد العمل ثابتا بالكتابة",
        "محرراً باللغة العربية",
        "محررا باللغة العربية",
        "نسختين لكل طرف",
        "مدة العقد",
    ],

    "wages": [
        "wage",
        "wages",
        "salary",
        "pay",
        "payment of salary",
        "compensation",
        "remuneration",
        "الأجر",
        "الاجر",
        "الأجور",
        "الاجور",
        "الراتب",
        "راتب",
        "أجر",
        "اجر",
        "بدل",
        "العلاوات",
        "المكافآت",
    ],

      "working_hours": [
        "working hours",
        "work hours",
        "hours of work",

        "overtime",
        "overtime work",
        "overtime hours",
        "additional working hours",

        "ساعات العمل",
        "ساعة العمل",

        "العمل الإضافي",
        "العمل الاضافي",

        "ساعات العمل الإضافية",
        "ساعات العمل الاضافية",

        "ساعات عمل إضافية",
        "ساعات عمل اضافية",

        "ساعات إضافية",
        "ساعات اضافية",

        "فترات الراحة",
        "فترة الراحة",
        "الراحة",
    ],

    "annual_leave": [
        "annual leave",
        "paid leave",
        "vacation",
        "holiday",
        "leave entitlement",
        "الإجازة السنوية",
        "الاجازة السنوية",
        "إجازة سنوية",
        "اجازة سنوية",
        "الإجازات",
        "الاجازات",
        "العطلات",
    ],

    "sick_leave": [
        "sick leave",
        "medical leave",
        "إجازة مرضية",
        "اجازة مرضية",
        "الإجازة المرضية",
        "الاجازة المرضية",
        "المرض",
    ],

    "termination": [
        "termination",
        "termination employment",
        "employment termination",
        "end of employment",
        "dismissal",
        "notice period",
        "notice",
        "إنهاء عقد العمل",
        "انهاء عقد العمل",
        "إنهاء العقد",
        "انهاء العقد",
        "الفصل",
        "مهلة الإخطار",
        "مهلة الاخطار",
        "الإخطار",
        "الاخطار",
    ],

    "probation": [
        "probation",
        "probation period",
        "trial period",
        "فترة التجربة",
        "شرط التجربة",
        "التجربة",
    ],

    "end_of_service": [
    "end of service",
    "end of service benefit",
    "end of service benefits",
    "end of service rights",
    "severance",
    "severance benefit",
    "termination benefit",
    "termination benefits",

    "مكافأة نهاية الخدمة",
    "مكافاه نهاية الخدمة",
    "نهاية الخدمة",
    "مستحقات نهاية الخدمة",
    "مستحقات العامل",

    "عند إنهاء عقد العمل",
    "عند انتهاء عقد العمل",
    "إنهاء عقد العمل",
    "انتهاء عقد العمل",

    "يستحق العامل",
    "سنوات العمل",
    "سنوات الخدمة",

    "أجر نصف شهر",
    "اجر نصف شهر",
    "أجر شهر عن كل سنة",
    "اجر شهر عن كل سنة",

    "غير الخاضع لأحكام قانون التأمين الاجتماعي",
    "غير الخاضع لقانون التأمين الاجتماعي",
    "التأمين الاجتماعي",
],
    "disciplinary": [
        "disciplinary",
        "disciplinary sanctions",
        "employee warning",
        "warning letter",
        "misconduct",
        "جزاء",
        "الجزاءات",
        "جزاءات تأديبية",
        "الجزاءات التأديبية",
        "مخالفة",
        "إنذار",
        "انذار",
    ],

    "confidentiality": [
        "confidentiality",
        "confidential information",
        "non disclosure",
        "non-disclosure",
        "nda",
        "سرية",
        "السرية",
        "سرية المعلومات",
        "المعلومات السرية",
        "عدم الإفصاح",
        "عدم الافصاح",
    ],

    "personal_data": [
        "personal data",
        "data protection",
        "personal information",
        "privacy",
        "processing personal data",
        "بيانات شخصية",
        "البيانات الشخصية",
        "حماية البيانات",
        "معالجة البيانات",
        "معالجه البيانات",
        "الخصوصية",
    ],

    "data_security": [
        "data security",
        "security measures",
        "information security",
        "confidentiality of processing",
        "أمن البيانات",
        "امن البيانات",
        "سرية المعالجة",
        "سريه المعالجه",
        "التدابير الفنية",
        "التدابير التنظيمية",
    ],

    "data_transfer": [
        "data transfer",
        "international data transfer",
        "cross border data transfer",
        "transfer personal data",
        "نقل البيانات",
        "نقل البيانات الشخصية",
        "خارج المملكة",
    ],

    "employee": [
        "employee",
        "worker",
        "staff",
        "العامل",
        "الموظف",
        "عمال",
    ],

    "employer": [
        "employer",
        "company",
        "organization",
        "صاحب العمل",
        "المنشأة",
        "الشركة",
    ],

    "contract": [
        "contract",
        "agreement",
        "عقد",
        "اتفاق",
        "اتفاقية",
    ],

    "obligations": [
        "obligation",
        "obligations",
        "duties",
        "responsibilities",
        "التزام",
        "التزامات",
        "واجبات",
        "مسؤوليات",
    ],
}


def load_regulations() -> list[dict[str, Any]]:
    """
    Load Bahrain regulations from the local
    trusted knowledge base.
    """

    if not REGULATIONS_FILE.exists():
        raise FileNotFoundError(
            "Bahrain regulations knowledge base "
            "was not found."
        )

    with open(
        REGULATIONS_FILE,
        "r",
        encoding="utf-8",
    ) as file:
        raw_data: Any = json.load(file)

    if not isinstance(raw_data, dict):
        raise ValueError(
            "Invalid regulations knowledge base."
        )

    data = cast(
        dict[str, Any],
        raw_data,
    )

    raw_regulations: Any = data.get(
        "regulations",
        [],
    )

    if not isinstance(
        raw_regulations,
        list,
    ):
        return []

    return cast(
        list[dict[str, Any]],
        raw_regulations,
    )


def normalize_text(
    text: str,
) -> str:
    """
    Normalize Arabic and English text.
    """

    text = text.lower()

    # Arabic letter normalization.
    text = re.sub(
        r"[أإآٱ]",
        "ا",
        text,
    )

    text = text.replace(
        "ى",
        "ي",
    )

    text = text.replace(
        "ة",
        "ه",
    )

    text = text.replace(
        "ؤ",
        "و",
    )

    text = text.replace(
        "ئ",
        "ي",
    )

    # Remove tatweel.
    text = text.replace(
        "ـ",
        "",
    )

    # Remove Arabic diacritics.
    text = re.sub(
        r"[\u064B-\u065F\u0670]",
        "",
        text,
    )

    # Normalize hyphens.
    text = text.replace(
        "-",
        " ",
    )

    # Remove punctuation.
    text = re.sub(
        r"[^\w\s]",
        " ",
        text,
    )

    # Normalize whitespace.
    text = re.sub(
        r"\s+",
        " ",
        text,
    ).strip()

    return text

def normalize_match_word(
    word: str,
) -> str:
    """
    Light normalization for matching Arabic
    word variants without changing stored law text.

    Examples:
    العمل -> عمل
    الإضافي -> اضاف
    إضافية -> اضاف
    """

    word = normalize_text(
        word
    )

    # Remove Arabic definite article.
    if (
        word.startswith("ال")
        and len(word) > 4
    ):
        word = word[2:]

    # Light handling of common adjective endings.
    if (
        word.endswith("يه")
        and len(word) > 4
    ):
        word = word[:-2]

    elif (
        word.endswith("ي")
        and len(word) > 4
    ):
        word = word[:-1]

    return word


def get_query_words(
    query: str,
) -> list[str]:

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
    query: str,
) -> list[str]:

    words = get_query_words(
        query
    )

    phrases: list[str] = []

    for index in range(
        len(words) - 1
    ):
        phrases.append(
            f"{words[index]} "
            f"{words[index + 1]}"
        )

    for index in range(
        len(words) - 2
    ):
        phrases.append(
            f"{words[index]} "
            f"{words[index + 1]} "
            f"{words[index + 2]}"
        )

    return phrases


def detect_legal_concepts(
    query: str,
) -> list[str]:
    """
    Detect legal concepts from either
    Arabic or English queries.
    """

    normalized_query = normalize_text(
        query
    )

    detected: list[str] = []

    for concept, terms in (
        LEGAL_CONCEPTS.items()
    ):

        for term in terms:

            normalized_term = normalize_text(
                term
            )

            if (
                normalized_term
                and normalized_term
                in normalized_query
            ):
                detected.append(
                    concept
                )
                break

    return detected


def get_expanded_terms(
    query: str,
) -> list[str]:
    """
    Expand an English or Arabic legal query
    using the bilingual concept map.
    """

    expanded: list[str] = []

    # Original query.
    normalized_query = normalize_text(
        query
    )

    if normalized_query:
        expanded.append(
            normalized_query
        )

    # Original words.
    for word in get_query_words(
        query
    ):
        if word not in expanded:
            expanded.append(
                word
            )

    # Bilingual legal concepts.
    concepts = detect_legal_concepts(
        query
    )

    for concept in concepts:

        terms = LEGAL_CONCEPTS.get(
            concept,
            [],
        )

        for term in terms:

            normalized_term = normalize_text(
                term
            )

            if (
                normalized_term
                and normalized_term
                not in expanded
            ):
                expanded.append(
                    normalized_term
                )

    return expanded


def is_repealed_regulation(
    regulation: dict[str, Any],
) -> bool:
    """
    Ignore provisions clearly marked
    as repealed in the knowledge base.
    """

    text = normalize_text(
        str(
            regulation.get(
                "text",
                "",
            )
        )
    )

    repealed_markers = {
        normalize_text("ملغى"),
        normalize_text("-ملغى-"),
        normalize_text("repealed"),
    }

    return (
        text in repealed_markers
    )


def calculate_score(
    query: str,
    regulation: dict[str, Any],
) -> int:
    """
    Calculate legal relevance using:
    - bilingual concepts
    - phrases
    - individual words
    - title/category matches
    - concept coverage
    """

    if is_repealed_regulation(
        regulation
    ):
        return 0

    query_normalized = normalize_text(
        query
    )

    query_words = get_query_words(
        query
    )

    query_phrases = get_query_phrases(
        query
    )

    expanded_terms = get_expanded_terms(
        query
    )

    detected_concepts = (
        detect_legal_concepts(
            query
        )
    )

    title = normalize_text(
        str(
            regulation.get(
                "title",
                "",
            )
        )
    )

    text = normalize_text(
        str(
            regulation.get(
                "text",
                "",
            )
        )
    )

    category = normalize_text(
        str(
            regulation.get(
                "category",
                "",
            )
        )
    )

    searchable_text = (
        f"{title} "
        f"{category} "
        f"{text}"
    )

    score = 0

    matched_original_words = 0
    matched_expanded_terms = 0
    matched_concepts = 0

    # ---------------------------------------------
    # Exact original query
    # ---------------------------------------------

    if (
        query_normalized
        and query_normalized
        in text
    ):
        score += 35

    # ---------------------------------------------
    # Original phrases
    # ---------------------------------------------

    for phrase in query_phrases:

        if phrase in text:

            phrase_length = len(
                phrase.split()
            )

            if phrase_length >= 3:
                score += 16
            else:
                score += 10

    # ---------------------------------------------
    # Original query words
    # ---------------------------------------------

    for word in query_words:

        matched = False

        if word in text:
            score += 4
            matched = True

        if word in title:
            score += 2
            matched = True

        if word in category:
            score += 4
            matched = True

        if matched:
            matched_original_words += 1

        # ---------------------------------------------
    # Expanded bilingual legal terms
    # ---------------------------------------------
    #
    # Original query terms already receive strong
    # scoring above.
    #
    # Concept-expanded terms are supporting evidence,
    # so they must not overpower a direct match to
    # the user's original legal query.
    # ---------------------------------------------

    original_terms: set[str] = set(
        query_words
    )

    if query_normalized:
        original_terms.add(
            query_normalized
        )

    for term in expanded_terms:

        if not term:
            continue

        # The original query and its own words
        # were already scored above.
        # Do not score them a second time here.
        if term in original_terms:
            continue

        if term in text:

            term_word_count = len(
                term.split()
            )

            # Expanded phrases are useful supporting
            # evidence, but deliberately receive less
            # weight than direct query matches.
            if term_word_count >= 4:
                score += 6

            elif term_word_count == 3:
                score += 5

            elif term_word_count == 2:
                score += 3

            else:
                score += 1

            matched_expanded_terms += 1

        # Title/category expansion is intentionally
        # kept very small.
        if term in title:
            score += 1

        if term in category:
            score += 1
   

     # ---------------------------------------------
    # Legal concept matching
    # ---------------------------------------------
    #
    # A regulation should receive stronger support
    # when it contains concept phrases that are
    # close to the user's original query.
    #
    # Example:
    # "العمل الإضافي"
    # should favour:
    # "ساعات عمل إضافية"
    #
    # more than:
    # "فترات الراحة"
    #
    # Both belong to the broader working-hours
    # concept, but they do not express the same
    # subtopic.
    # ---------------------------------------------

    query_word_set = {
        normalize_match_word(word)
        for word in query_words
        if normalize_match_word(word)
    }
    

    for concept in detected_concepts:

        concept_terms = (
            LEGAL_CONCEPTS.get(
                concept,
                [],
            )
        )

        concept_found = False
        best_concept_similarity = 0

        for term in concept_terms:

            normalized_term = normalize_text(
                term
            )

            if not normalized_term:
                continue

            if normalized_term not in searchable_text:
                continue

            concept_found = True

            term_words = {
                normalize_match_word(word)
                for word in normalized_term.split()
                if normalize_match_word(word)
            }

            if not term_words:
                continue

            shared_words = (
                query_word_set
                & term_words
            )

            if not shared_words:
                continue

            query_coverage = (
                len(shared_words)
                / max(
                    len(query_word_set),
                    1,
                )
            )

            term_coverage = (
                len(shared_words)
                / len(term_words)
            )

            similarity = int(
                (
                    query_coverage
                    * 12
                )
                +
                (
                    term_coverage
                    * 8
                )
            )

            # Strong bonus when a concept phrase
            # preserves all meaningful words from
            # the user's original query.
            #
            # Example:
            # Query: العمل الإضافي
            # Text term: ساعات عمل إضافية
            #
            # This is much more specific than a
            # generic match such as ساعات العمل.
            if (
                query_word_set
                and query_word_set.issubset(
                    term_words
                )
            ):
                similarity += 25

            best_concept_similarity = max(
                best_concept_similarity,
                similarity,
            )

        if concept_found:

            # Base concept support.
            score += 10

            # Extra support for the concept phrase
            # that is closest to the original query.
            score += best_concept_similarity

            matched_concepts += 1

    # ---------------------------------------------
    # Original word coverage
    # ---------------------------------------------

    total_original_words = len(
        query_words
    )

    if total_original_words > 0:

        coverage = (
            matched_original_words
            / total_original_words
        )

        if coverage >= 1:
            score += 15

        elif coverage >= 0.75:
            score += 10

        elif coverage >= 0.50:
            score += 5

    # ---------------------------------------------
    # Concept coverage
    # ---------------------------------------------

    total_concepts = len(
        detected_concepts
    )

    if total_concepts > 0:

        concept_coverage = (
            matched_concepts
            / total_concepts
        )

        if concept_coverage >= 1:
            score += 20

        elif concept_coverage >= 0.50:
            score += 10

    # ---------------------------------------------
    # Minimum relevance protection
    # ---------------------------------------------

    if (
        matched_original_words == 0
        and matched_expanded_terms == 0
        and matched_concepts == 0
    ):
        return 0

    return score


def search_regulations(
    query: str,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """
    Search the trusted Bahrain regulations
    knowledge base.

    Supports Arabic and English legal queries.
    """

    if not query.strip():
        return []

    regulations = load_regulations()

    results: list[
        dict[str, Any]
    ] = []

    detected_concepts = (
        detect_legal_concepts(
            query
        )
    )

    for regulation in regulations:

        score = calculate_score(
            query=query,
            regulation=regulation,
        )

        if score <= 0:
            continue

        result = regulation.copy()

        result[
            "relevance_score"
        ] = score

        result[
            "matched_concepts"
        ] = detected_concepts

        results.append(
            result
        )

    results.sort(
        key=lambda item: int(
            item.get(
                "relevance_score",
                0,
            )
        ),
        reverse=True,
    )

    return results[:limit]