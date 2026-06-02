from graph import graph

query = input("\nEnter research topic: ")

result = graph.invoke(
    {
        "query": query
    }
)

print("\n=== REPORT ===\n")
print(result["formatted_report"])