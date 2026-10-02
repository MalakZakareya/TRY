from services.nea_importer import (
    build_nea_knowledge_base,
)


print("Building NEA knowledge base...")
print("-" * 50)

standards = build_nea_knowledge_base()

print("NEA knowledge base created successfully.")
print("Total standards:", len(standards))

print("\nFirst 10 parsed standards:")
print("-" * 50)

for standard in standards[:10]:
    print(
        standard["section_number"],
        "-",
        standard["title"],
    )

print("-" * 50)
print(
    "Saved to: "
    "knowledge/bahrain/nea/standards.json"
)