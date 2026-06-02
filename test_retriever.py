from rag.retriever import retrieve

results = retrieve(
    "What is LangGraph?"
)

print("\nRESULTS:\n")

for result in results:

    print(result)
    print("-" * 50)