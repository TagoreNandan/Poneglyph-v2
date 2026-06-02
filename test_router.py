from agents.router_agent import classify_query

queries = [
    "Latest AI news",
    "What is LangGraph?",
    "Compare LangGraph with latest AI agent frameworks"
]

for query in queries:

    route = classify_query(query)

    print()
    print(query)
    print("→", route)