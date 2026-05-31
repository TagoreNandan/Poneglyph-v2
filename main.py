from agents.search_agent import search_web

results = search_web(
    "Latest developments in Retrieval-Augmented Generation"
)

for i, result in enumerate(results, 1):
    print(f"\n{i}. {result['title']}")
    print(result['url'])