from services.nea_retriever import (
    retrieve_design_requirements,
)


detected_elements = [
    "colors",
    "contrast",
    "logo",
    "navigation",
    "links",
]

print("Testing NEA Retriever...")
print("-" * 60)

results = retrieve_design_requirements(
    detected_elements=detected_elements,
    limit_per_element=3,
)

print("Total retrieved requirements:", len(results))
print("-" * 60)

for result in results:
    print(
        "\nDetected element:",
        result["matched_element"],
    )

    print(
        "Section:",
        result["section_number"],
    )

    print(
        "Title:",
        result["title"],
    )

    print(
        "Score:",
        result["relevance_score"],
    )

    print("-" * 60)