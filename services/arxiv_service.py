import logging
from typing import List, Dict, Any
import arxiv

logger = logging.getLogger(__name__)

def search_arxiv(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Search the ArXiv database for academic papers matching the query.
    
    Args:
        query: The search query string.
        max_results: The maximum number of results to return.
        
    Returns:
        A list of dictionaries containing structured metadata of the papers:
        - title: The paper's title.
        - summary: The abstract/summary.
        - authors: A list of author names.
        - published_date: The publication date as a string (YYYY-MM-DD).
        - pdf_url: The direct link to the PDF.
        - arxiv_url: The ArXiv entry detail URL.
        - primary_category: The primary subject category of the paper.
    """
    logger.info("Starting ArXiv search for query: '%s' with max_results=%d", query, max_results)
    
    if not query or not query.strip():
        logger.warning("Empty search query provided to search_arxiv")
        return []
        
    try:
        client = arxiv.Client()
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance
        )
        
        results = []
        for result in client.results(search):
            try:
                published_date_str = ""
                if result.published:
                    published_date_str = result.published.strftime("%Y-%m-%d")
                
                paper_dict = {
                    "title": result.title,
                    "summary": result.summary,
                    "authors": [author.name for author in result.authors],
                    "published_date": published_date_str,
                    "pdf_url": result.pdf_url,
                    "arxiv_url": result.entry_id,
                    "primary_category": result.primary_category
                }
                results.append(paper_dict)
            except Exception as e:
                logger.error("Failed to parse a specific ArXiv search result: %s", e, exc_info=True)
                continue
                
        logger.info("Successfully retrieved %d ArXiv results for query: '%s'", len(results), query)
        return results
        
    except Exception as e:
        logger.error("Failed to perform ArXiv search: %s", e, exc_info=True)
        return []
