import os
import json
from tavily import TavilyClient
from dotenv import load_dotenv
from llm.gemini_client import generate as gemini_generate

load_dotenv()

client = TavilyClient(
    api_key=os.getenv(
        "TAVILY_API_KEY"
    )
)

def expand_queries(topic: str) -> list:
    prompt = f"""
Given the research topic: "{topic}", extract the core intent and generate exactly 3 distinct search queries optimized for search engines to retrieve highly relevant research content.
Each search query should explore a different facet of the topic (e.g. key figures, historical periods, technical concepts, or specific subtopics).
Do not include any numbering, quotes, or category labels. Output exactly 3 queries, one per line.
"""
    try:
        response = gemini_generate(prompt).strip()
        queries = [q.strip() for q in response.split("\n") if q.strip()]
        queries = [q for q in queries if len(q) < 100]
        if queries:
            return queries[:3]
    except Exception as e:
        print(f"Failed to expand query: {e}")
    return [topic]

def batch_score_sources(query: str, sources: list) -> list:
    if not sources:
        return []
    
    formatted_sources = []
    for idx, s in enumerate(sources):
        title = s.get("title", "No Title")
        snippet = s.get("content", "")[:300]
        formatted_sources.append(f"[{idx}] Title: {title}\nSnippet: {snippet}\n")
        
    prompt = f"""
You are a research quality assistant. Evaluate the semantic relevance of the following search results to the query.
Query: "{query}"

Search Results:
{"-" * 40}
{"".join(formatted_sources)}
{"-" * 40}

For each search result, assign a score from 0 to 10 based on its relevance to the query:
- 10: Perfectly relevant, directly answers the core topic.
- 7-9: Highly relevant, provides core information about the query.
- 4-6: Partially relevant or related context, but doesn't focus on the main topic.
- 0-3: Completely irrelevant, unrelated domain, or spam (e.g. "crystal growth" or "Indian monsoon" for a query about "Indian cinema growth").

Output the scores as a JSON array of objects, containing ONLY "id" (the index number) and "score" (the assigned integer).
Example output:
[
  {{"id": 0, "score": 8}},
  {{"id": 1, "score": 2}}
]
Do not output any explanation or extra text. Output ONLY the JSON block.
"""
    scores = {i: 0 for i in range(len(sources))}
    try:
        response = gemini_generate(prompt).strip()
        start = response.find("[")
        end = response.rfind("]")
        if start != -1 and end != -1 and end > start:
            parsed = json.loads(response[start:end+1])
            for item in parsed:
                idx = item.get("id")
                score = item.get("score", 0)
                if idx is not None and 0 <= idx < len(sources):
                    scores[idx] = score
    except Exception as e:
        print(f"Batch scoring failed: {e}")
        return [5] * len(sources) # Default fallback
        
    return [scores[i] for i in range(len(sources))]

def search_web(query):
    print(f"Running single Tavily search for: '{query}'")
    try:
        res = client.search(
            query=query,
            search_depth="advanced",
            max_results=8,
            include_raw_content=True
        )
        all_results = res.get("results", [])
    except Exception as e:
        print(f"Tavily search failed: {e}")
        return []

    if not all_results:
        return []

    # Score and Filter sources
    scores = batch_score_sources(query, all_results)
    
    filtered_results = []
    for idx, r in enumerate(all_results):
        score = scores[idx] if idx < len(scores) else 0
        r["relevance_score"] = score
        if score >= 5:
            filtered_results.append(r)
            
    # If filtering returned absolutely nothing, fallback to top 3 results of original query to be robust
    if not filtered_results and all_results:
        print("Warning: All results filtered out. Falling back to top 3 unfiltered results.")
        filtered_results = all_results[:3]
        
    # Sort by score descending and return top 5
    filtered_results = sorted(filtered_results, key=lambda x: x.get("relevance_score", 0), reverse=True)
    return filtered_results[:5]