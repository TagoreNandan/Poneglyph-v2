import arxiv
import json
from llm.gemini_client import generate as gemini_generate

def expand_academic_queries(topic: str) -> list:
    prompt = f"""
Given the academic research topic: "{topic}", generate exactly 2 distinct search queries optimized for the arXiv database.
ARXiv expects technical terms, key mathematical concepts, or scientific methodologies.
Do not include any numbering, quotes, or category labels. Output exactly 2 queries, one per line.
"""
    try:
        try:
            response = gemini_generate(prompt).strip()
        except Exception as gemini_err:
            import logging
            logging.getLogger(__name__).warning("ArXiv Agent (expand_academic_queries): Gemini call failed. Activating Groq fallback.", exc_info=True)
            from llm.groq_client import generate as groq_generate
            response = groq_generate(prompt).strip()

        queries = [q.strip() for q in response.split("\n") if q.strip()]
        queries = [q for q in queries if len(q) < 100]
        if queries:
            return queries[:2]
    except Exception as e:
        print(f"Failed to expand academic query: {e}")
    return [topic]

def batch_score_papers(query: str, papers: list) -> list:
    if not papers:
        return []
    
    formatted_papers = []
    for idx, p in enumerate(papers):
        title = p.get("title", "No Title")
        summary = p.get("summary", "")[:300]
        formatted_papers.append(f"[{idx}] Title: {title}\nSummary: {summary}\n")
        
    prompt = f"""
You are a research quality assistant. Evaluate the relevance of the following academic papers to the research topic.
Topic: "{query}"

Academic Papers:
{"-" * 40}
{"".join(formatted_papers)}
{"-" * 40}

For each paper, assign a relevance score from 0 to 10 based on its technical alignment with the topic:
- 10: Perfect fit, specifically addresses the topic.
- 7-9: Highly relevant technical paper.
- 4-6: Partially relevant or related context, but doesn't focus on the main topic.
- 0-3: Completely irrelevant (e.g. a physics paper about "crystal growth" for a cinema or economics topic).

Output the scores as a JSON array of objects, containing ONLY "id" (index) and "score" (integer).
Example output:
[
  {{"id": 0, "score": 8}},
  {{"id": 1, "score": 2}}
]
Do not output any explanation or extra text. Output ONLY the JSON block.
"""
    scores = {i: 0 for i in range(len(papers))}
    try:
        try:
            response = gemini_generate(prompt).strip()
        except Exception as gemini_err:
            import logging
            logging.getLogger(__name__).warning("ArXiv Agent (batch_score_papers): Gemini call failed. Activating Groq fallback.", exc_info=True)
            from llm.groq_client import generate as groq_generate
            response = groq_generate(prompt).strip()

        start = response.find("[")
        end = response.rfind("]")
        if start != -1 and end != -1 and end > start:
            parsed = json.loads(response[start:end+1])
            for item in parsed:
                idx = item.get("id")
                score = item.get("score", 0)
                if idx is not None and 0 <= idx < len(papers):
                    scores[idx] = score
    except Exception as e:
        print(f"Batch scoring papers failed: {e}")
        return [5] * len(papers)
        
    return [scores[i] for i in range(len(papers))]

def search_arxiv(
    query: str,
    max_results: int = 5
):
    print(f"Running single arXiv search for: '{query}'")
    
    client = arxiv.Client()
    seen_urls = set()
    all_papers = []
    
    try:
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance
        )
        for paper in client.results(search):
            url = paper.pdf_url
            if url not in seen_urls:
                seen_urls.add(url)
                all_papers.append({
                    "title": paper.title,
                    "summary": paper.summary,
                    "authors": [author.name for author in paper.authors],
                    "published": str(paper.published.date()),
                    "url": url,
                    "source": "arxiv"
                })
    except Exception as e:
        print(f"arXiv query failed for '{query}': {e}")
            
    if not all_papers:
        print("arXiv results count: 0")
        print("Ranked papers count: 0")
        print("Final selected papers count: 0")
        return []

    # Score and filter
    try:
        scores = batch_score_papers(query, all_papers)
    except Exception as e:
        print(f"Batch scoring papers failed: {e}")
        scores = [5] * len(all_papers)

    # If scoring failed completely (e.g. returned all zeros due to API error or parsing error), fail-open
    if all(s == 0 for s in scores):
        print("Warning: Paper scoring failed or returned all zeros. Failing open with default scores.")
        scores = [5] * len(all_papers)
        
    filtered_papers = []
    for idx, p in enumerate(all_papers):
        score = scores[idx] if idx < len(scores) else 0
        p["relevance_score"] = score
        if score >= 5:
            filtered_papers.append(p)
            
    # If filtering returned absolutely nothing, fallback to all raw papers (fail-open)
    if not filtered_papers and all_papers:
        print("Warning: All papers filtered out. Failing open to all raw papers.")
        for p in all_papers:
            p["relevance_score"] = 5
        filtered_papers = all_papers

    final_papers = sorted(filtered_papers, key=lambda x: x.get("relevance_score", 0), reverse=True)[:max_results]

    print(f"arXiv results count: {len(all_papers)}")
    print(f"Ranked papers count: {len(filtered_papers)}")
    print(f"Final selected papers count: {len(final_papers)}")

    return final_papers