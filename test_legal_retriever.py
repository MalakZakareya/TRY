from services.legal_retriever import search_regulations


query = "التمييز بين العمال"

print("Searching Bahrain regulations...")
print("Query:", query)
print()


results = search_regulations(query)


print("Results found:", len(results))
print()


for result in results[:5]:

    print("------------------------------")
    print("Article:", result["article"])
    print("Title:", result["title"])
    print(
        "Relevance score:",
        result["relevance_score"]
    )
    print()
    print(result["text"][:500])
    print()