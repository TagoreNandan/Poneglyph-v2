# test_arxiv_simple.py

import arxiv

client = arxiv.Client()

search = arxiv.Search(
    query="machine learning",
    max_results=1
)

for result in client.results(search):
    print(result.title)