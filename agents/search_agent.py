import os
import json
import requests
from tavily import TavilyClient
from dotenv import load_dotenv
from llm.gemini_client import generate as gemini_generate

load_dotenv()

client = TavilyClient(
    api_key=os.getenv(
        "TAVILY_API_KEY"
    )
)

TRUST_BOOSTS = {
    "openai.com": 30,
    "anthropic.com": 30,
    "deepmind.google": 30,
    "google.com": 20,
    "arxiv.org": 25,
    "nature.com": 25,
    "reuters.com": 25,
    "bloomberg.com": 25,
    "wsj.com": 20,
    "ft.com": 20,
    "sec.gov": 30,
    "github.com": 15
}

TRUST_PENALTIES = {
    "reddit.com": -25,
    "youtube.com": -20,
    "instagram.com": -50,
    "tiktok.com": -50,
    "facebook.com": -50,
    "pinterest.com": -50
}

from urllib.parse import urlparse
import re
import datetime

SOURCE_AUTHORITY = {
    "official": 95,
    "government": 90,
    "research": 90,
    "major_news": 85,
    "wikipedia": 80,
    "industry": 75,
    "community": 50,
    "reddit": 40,
    "youtube": 35,
    "soundcloud": 10
}

def is_entertainment_topic(query: str) -> bool:
    normalized = query.lower()
    entertainment_keywords = [
        "anime", "manga", "game", "gaming", "playstation", "xbox", "nintendo", "zelda", "mario", "pokemon",
        "bleach", "naruto", "one piece", "wano", "marineford", "luffy", "zoro", "kaido", "ichigo",
        "senbon zakura", "bankai", "shinigami", "soul society", "autobot", "decepticon", "transformers",
        "cybertron", "optimus", "megatron", "g1", "goku", "vegeta", "dragon ball", "movie", "film",
        "show", "series", "music", "song", "track", "soundcloud", "band", "soundtrack", "entertainment",
        "character", "boss", "level", "campaign", "multiplayer", "cosplay", "fandom", "otaku",
        "hollow", "arrancar", "espada", "quincy", "gotei", "shikai", "zanpakuto", "jujutsu", "kaisen",
        "demon slayer", "tanjiro", "nezuko", "hacker", "retro", "nostalgia", "consoles"
    ]
    return any(kw in normalized for kw in entertainment_keywords)

def get_authority_score(url: str) -> float:
    if not url:
        return SOURCE_AUTHORITY["community"]
        
    url_lower = url.lower()
    domain = url_lower.split("://")[-1].split("/")[0].split("?")[0]
    if domain.startswith("www."):
        domain = domain[4:]
        
    # Check specific domains first
    if "reddit.com" in domain:
        return SOURCE_AUTHORITY["reddit"]
    if "youtube.com" in domain or "youtu.be" in domain:
        return SOURCE_AUTHORITY["youtube"]
    if "soundcloud.com" in domain:
        return SOURCE_AUTHORITY["soundcloud"]
    if "fandom.com" in domain:
        return SOURCE_AUTHORITY["community"]
    if "wikipedia.org" in domain:
        return SOURCE_AUTHORITY["wikipedia"]
        
    # Check trusted lists
    official_domains = ["openai.com", "anthropic.com", "google.com", "microsoft.com", "nvidia.com", "tesla.com", "deepmind.google"]
    if any(d == domain or domain.endswith("." + d) for d in official_domains) or ".gov" in domain:
        if ".gov" in domain:
            return SOURCE_AUTHORITY["government"]
        return SOURCE_AUTHORITY["official"]
        
    academic_domains = ["arxiv.org", "nature.com", "science.org", "coursera.org"]
    if any(d == domain or domain.endswith("." + d) for d in academic_domains) or ".edu" in domain:
        return SOURCE_AUTHORITY["research"]
        
    news_domains = ["reuters.com", "bloomberg.com", "ft.com", "wsj.com", "cnbc.com", "cnn.com"]
    if any(d == domain or domain.endswith("." + d) for d in news_domains):
        return SOURCE_AUTHORITY["major_news"]
        
    tech_domains = ["techcrunch.com", "theverge.com", "wired.com", "github.com"]
    if any(d == domain or domain.endswith("." + d) for d in tech_domains):
        return SOURCE_AUTHORITY["industry"]
        
    # Check generic indicators
    if any(x in domain for x in ["forum", "forums", "community", "stackexchange", "stackoverflow", "quora"]):
        return SOURCE_AUTHORITY["community"]
        
    # Check generic blogging/writing networks
    if any(x in domain for x in ["blogspot", "wordpress", "medium.com", "substack.com"]):
        return SOURCE_AUTHORITY["community"]
        
    return SOURCE_AUTHORITY["industry"]

def domain_score(url: str) -> int:
    try:
        domain = urlparse(url).netloc.lower()
    except:
        return 0

    for trusted, boost in TRUST_BOOSTS.items():
        if trusted in domain:
            return boost

    for bad, penalty in TRUST_PENALTIES.items():
        if bad in domain:
            return penalty

    return 0

def extract_domain(url: str) -> str:
    try:
        domain = urlparse(url).netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except:
        return ""

def get_freshness_score(result: dict) -> float:
    current_year = datetime.datetime.now().year
    pub_date = result.get("published_date")
    year = None
    if pub_date:
        try:
            match = re.search(r'\b(20[0-2][0-9])\b', str(pub_date))
            if match:
                year = int(match.group(1))
        except:
            pass
            
    if not year:
        url = result.get("url", "")
        url_years = re.findall(r'/20[0-2][0-9]/', url)
        if url_years:
            year = int(url_years[0].strip('/'))
            
    if not year:
        content = result.get("content", "") + " " + result.get("title", "")
        content_years = re.findall(r'\b(20[0-2][0-9])\b', content)
        if content_years:
            valid_years = [int(y) for y in content_years if int(y) <= current_year]
            if valid_years:
                year = max(valid_years)
                
    if not year:
        return 7.0
        
    diff = current_year - year
    if diff <= 0:
        return 10.0
    elif diff == 1:
        return 9.0
    elif diff == 2:
        return 8.0
    elif diff == 3:
        return 7.0
    elif diff == 4:
        return 6.0
    elif diff == 5:
        return 5.0
    else:
        return 3.0

def expand_queries(topic: str) -> list:
    prompt = f"""
Given the research topic: "{topic}", extract the core intent and generate exactly 3 distinct search queries optimized for search engines to retrieve highly relevant research content.
Each search query should explore a different facet of the topic (e.g. key figures, historical periods, technical concepts, or specific subtopics).
Do not include any numbering, quotes, or category labels. Output exactly 3 queries, one per line.
"""
    try:
        try:
            response = gemini_generate(prompt).strip()
        except Exception as gemini_err:
            import logging
            logging.getLogger(__name__).warning("Search Agent (expand_queries): Gemini call failed. Activating Groq fallback.", exc_info=True)
            from llm.groq_client import generate as groq_generate
            response = groq_generate(prompt).strip()

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
        try:
            response = gemini_generate(prompt).strip()
        except Exception as gemini_err:
            import logging
            logging.getLogger(__name__).warning("Search Agent (batch_score_sources): Gemini call failed. Activating Groq fallback.", exc_info=True)
            from llm.groq_client import generate as groq_generate
            response = groq_generate(prompt).strip()

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

def search_serper(query: str) -> list:
    serper_api_key = os.getenv("SERPER_API_KEY")
    if not serper_api_key:
        print("Warning: SERPER_API_KEY not found in environment variables.")
        return []
    
    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": serper_api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "q": query
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        results_data = response.json().get("organic", [])
        
        results = []
        for r in results_data:
            results.append({
                "title": r.get("title", ""),
                "url": r.get("link", ""),
                "content": r.get("snippet", ""),
                "raw_content": r.get("snippet", ""),
                "source": "serper"
            })
        print(f"Serper returned {len(results)} results")
        return results
    except Exception as e:
        print(f"Serper search failed: {e}")
        return []

def search_web(query):
    print("Using Tavily search")
    print(f"Running single Tavily search for: '{query}'")
    all_results = []
    use_serper_fallback = False
    try:
        res = client.search(
            query=query,
            search_depth="advanced",
            max_results=8,
            include_raw_content=True
        )
        all_results = res.get("results", [])
    except Exception as e:
        print("Tavily failed, switching to Serper")
        use_serper_fallback = True

    if use_serper_fallback:
        all_results = search_serper(query)

    if not all_results:
        print("Tavily results count: 0")
        print("Ranked results count: 0")
        print("Final selected results count: 0")
        return []

    # 2. HARD BLOCK LOW-QUALITY SOURCES
    BLOCKED_DOMAINS = {
        "instagram.com",
        "tiktok.com",
        "facebook.com",
        "pinterest.com"
    }
    filtered_raw = []
    for r in all_results:
        url = r.get("url") or ""
        if any(blocked in url.lower() for blocked in BLOCKED_DOMAINS):
            print(f"Blocked low-quality source: {url}")
            continue
        filtered_raw.append(r)
    all_results = filtered_raw

    if not all_results:
        print("Tavily results count: 0")
        print("Ranked results count: 0")
        print("Final selected results count: 0")
        return []

    # Score and Filter sources
    try:
        scores = batch_score_sources(query, all_results)
    except Exception as e:
        print(f"Batch scoring exception: {e}")
        scores = [5] * len(all_results)

    # If scoring failed completely (e.g. returned all zeros due to API error or parsing error), fail-open
    if all(s == 0 for s in scores):
        print("Warning: Source scoring failed or returned all zeros. Failing open with default scores.")
        scores = [5] * len(all_results)
    
    is_ent = is_entertainment_topic(query)
    filtered_results = []
    for idx, r in enumerate(all_results):
        score = scores[idx] if idx < len(scores) else 0
        r["relevance_score"] = score
        
        # Calculate scores
        freshness_score = get_freshness_score(r)
        r["freshness_score"] = freshness_score
        
        url = r.get("url", "")
        authority_score = get_authority_score(url)
        domain = extract_domain(url)
        
        if not is_ent:
            if "reddit.com" in domain:
                authority_score = max(0.0, authority_score - 40)
            elif "youtube.com" in domain or "youtu.be" in domain:
                authority_score = max(0.0, authority_score - 35)
            elif "soundcloud.com" in domain:
                authority_score = max(0.0, authority_score - 10)
            elif "fandom.com" in domain:
                authority_score = max(0.0, authority_score - 40)
                
        relevance_score_scaled = score * 10.0
        final_score = relevance_score_scaled * 0.60 + authority_score * 0.40
        r["final_score"] = final_score
        
        # Legacy domain_score for backward compatibility
        r["domain_score"] = domain_score(url)
        
        # Diagnostics
        print(f"Source domain: {domain}")
        print(f"Authority score: {authority_score}")
        print(f"Relevance score (scaled): {relevance_score_scaled}")
        print(f"Final ranking score: {final_score}")
        
        if score >= 5:
            filtered_results.append(r)
            
    # If filtering returned absolutely nothing, fallback to all raw results (fail-open)
    if not filtered_results and all_results:
        print("Warning: All results filtered out. Failing open to all raw results.")
        for r in all_results:
            r["relevance_score"] = 5
            freshness_score = get_freshness_score(r)
            r["freshness_score"] = freshness_score
            
            url = r.get("url", "")
            authority_score = get_authority_score(url)
            domain = extract_domain(url)
            
            if not is_ent:
                if "reddit.com" in domain:
                    authority_score = max(0.0, authority_score - 40)
                elif "youtube.com" in domain or "youtu.be" in domain:
                    authority_score = max(0.0, authority_score - 35)
                elif "soundcloud.com" in domain:
                    authority_score = max(0.0, authority_score - 10)
                elif "fandom.com" in domain:
                    authority_score = max(0.0, authority_score - 40)
                    
            relevance_score_scaled = 50.0  # 5 * 10
            final_score = relevance_score_scaled * 0.60 + authority_score * 0.40
            r["final_score"] = final_score
            
            # Legacy domain_score for backward compatibility
            r["domain_score"] = domain_score(url)
            
            # Diagnostics
            print(f"Source domain: {domain}")
            print(f"Authority score: {authority_score}")
            print(f"Relevance score (scaled): {relevance_score_scaled}")
            print(f"Final ranking score: {final_score}")
            
        filtered_results = all_results
        
    # Sort by final_score descending
    ranked_results = sorted(filtered_results, key=lambda x: x.get("final_score", 0), reverse=True)
    
    # 3. SOURCE DIVERSITY ENFORCEMENT
    selected = []
    seen_domains = set()
    for result in ranked_results:
        domain = extract_domain(result["url"])
        if domain in seen_domains:
            continue
        selected.append(result)
        seen_domains.add(domain)
        if len(selected) >= 5:
            break
            
    final_results = selected

    print("Selected Sources:")
    for src in final_results:
        print(f"- {src.get('url')}")
    
    print(f"Tavily results count: {len(all_results)}")
    print(f"Ranked results count: {len(filtered_results)}")
    print(f"Final selected results count: {len(final_results)}")
    
    return final_results