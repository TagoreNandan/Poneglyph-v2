import arxiv


def search_arxiv(
    query: str,
    max_results: int = 5
):

    client = arxiv.Client()

    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance
    )

    results = []

    for paper in client.results(search):

        results.append(
            {
                "title": paper.title,
                "summary": paper.summary,
                "authors": [
                    author.name
                    for author in paper.authors
                ],
                "published": str(
                    paper.published.date()
                ),
                "url": paper.pdf_url,
                "source": "arxiv"
            }
        )

    return results