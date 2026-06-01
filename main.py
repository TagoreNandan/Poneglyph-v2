from graph import graph

result = graph.invoke(
    {
        "query": "Latest developments in Retrieval-Augmented Generation"
    }
)

print("\n=== REPORT ===\n")
print(result["report"])