# test_router.py

from agents.router_agent import classify_query

queries = [
    "What is LangGraph?",
    "Latest AI news",
    "Compare LangGraph with latest AI agent frameworks",
    "Difference between LangGraph and current agent frameworks"
]

for query in queries:

    print()
    print(query)
    print("→", classify_query(query))