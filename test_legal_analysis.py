from services.legal_analysis_service import (
    retrieve_laws_for_points,
)


# Fake points that simulate points
# extracted from a real document
points = [
    {
        "point_number": 1,
        "title": "التمييز بين العمال",
        "category": "حقوق العمال",
        "original_text": (
            "يحظر التمييز بين العمال بسبب الجنس "
            "أو الأصل أو اللغة أو الدين أو العقيدة."
        ),
        "explanation": (
            "هذه النقطة تتعلق بمنع التمييز بين العمال."
        ),
    },
    {
        "point_number": 2,
        "title": "الأجر",
        "category": "الأجور",
        "original_text": (
            "يستحق العامل أجراً مقابل عمله."
        ),
        "explanation": (
            "هذه النقطة تتعلق بأجر العامل."
        ),
    },
    {
        "point_number": 3,
        "title": "إنهاء عقد العمل",
        "category": "إنهاء الخدمة",
        "original_text": (
            "يجوز لصاحب العمل إنهاء عقد العامل."
        ),
        "explanation": (
            "هذه النقطة تتعلق بإنهاء عقد العمل."
        ),
    },
]


print("Testing multiple document points...")
print()


results = retrieve_laws_for_points(
    points=points,
    limit_per_point=5,
)


for result in results:

    point = result["point"]

    print("=" * 60)
    print(
        "POINT:",
        point.get("point_number")
    )
    print(
        "TITLE:",
        point.get("title")
    )
    print()

    print(
        "REGULATIONS FOUND:",
        len(result["regulations"])
    )
    print()

    for regulation in result["regulations"]:

        print(
            "Article:",
            regulation["article"]
        )

        print(
            "Score:",
            regulation["relevance_score"]
        )

        print(
            regulation["text"][:250]
        )

        print("------------------------------")

    print()