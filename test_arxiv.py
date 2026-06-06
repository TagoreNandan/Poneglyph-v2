from agents.arxiv_agent import search_arxiv

results = search_arxiv(
    "Retrieval Augmented Generation"
)

print(results[0])