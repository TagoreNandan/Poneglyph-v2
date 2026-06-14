from typing import TypedDict, Dict, Any
import re
import urllib.parse

from langgraph.graph import StateGraph, END

from agents.search_agent import search_web
from agents.reader_agent import summarize_source
from agents.research_agent import generate_research_summary
from agents.writer_agent import format_report
from agents.critic_agent import review_report
from memory.database import save_research

from agents.router_agent import classify_query
from agents.ambiguity_agent import detect_ambiguity

#from rag.retriever import retrieve
#from agents.rag_answer_agent import generate_rag_answer

def get_source_priority(url: str, source_type: str = "web") -> int:
    if not url:
        return 5
    url = url.lower()
    if source_type == "arxiv" or ".gov" in url or ".edu" in url:
        return 1
    if ".org" in url or "official" in url:
        return 2
    if any(pub in url for pub in ["nytimes.com", "wsj.com", "bbc.co", "bbc.com", "reuters.com", "bloomberg.com", "guardian", "forbes", "nature.com"]):
        return 3
    if "wikipedia.org" in url:
        return 4
    if any(comm in url for comm in ["reddit.com", "stackexchange.com", "stackoverflow.com", "fandom.com", "quora.com", "forum"]):
        return 5
    return 3

def is_valid_evidence(text: str) -> bool:
    if not text:
        return False
    stripped = text.strip()
    if len(stripped) < 35:
        return False
    words = stripped.split()
    if len(words) < 6:
        return False
        
    # Complete sentence check:
    # 1. First character must be uppercase letter, digit, or quote
    if not (stripped[0].isupper() or stripped[0].isdigit() or stripped[0] in ['"', "'", "“", "‘"]):
        return False
    # 2. Must end with sentence punctuation, optionally followed by quotes/brackets/citations
    if not re.search(r'(?:[.!?]\s*(?:\[\d+\]|["\'”’]|\s)*|\[\d+\]\s*[.!?]\s*(?:["\'”’]|\s)*)$', stripped):
        return False
        
    text_lower = stripped.lower()
    junk = [
        "sign up", "log in", "sign in", "create account", "forgot password", "reset password",
        "log out", "logout", "signin", "signup", "login", "register", "logged in", "sign-up", "log-in",
        "skip navigation", "skip to main content", "navigation menu", "toggle navigation", "skip to content",
        "all rights reserved", "cookie policy", "privacy policy", "terms of service", "terms of use",
        "javascript is disabled", "enable javascript", "please check the url", "page not found",
        "404 error", "access denied", "reddit home", "youtube home", "subscribe now",
        "share this", "follow us", "comment below", "click here", "read more", "newsletter",
        "cookies on our website", "agree to our use", "accept all", "manage settings",
        "facebook", "twitter", "linkedin", "instagram", "pinterest", "reddit app", "youtube app",
        "menu", "dropdown", "navigation", "sidebar", "footer", "header", "copyright",
        "search on google", "google search", "web page", "web site", "browser", "refresh page",
        "user agreement", "privacy settings", "cookie settings", "privacy center", "cookie banner",
        "cookie notice", "privacy statement", "data protection", "tiktok", "snapchat", "discord",
        "telegram", "whatsapp", "share on", "tweet", "view on",
        "discussion in", "discussion thread", "started by", "thread starter", "posts:", "joined:",
        "table of contents", "table of content", "jump to navigation", "jump to search", "jump to content",
        "view history", "edit history", "page history", "sitemap", "site map"
    ]
    if any(pattern in text_lower for pattern in junk):
        return False
    if "http://" in text_lower or "https://" in text_lower or "www." in text_lower:
        return False
        
    return True

def calculate_quality_metrics(report: str, sources: list, current_year=2026):
    is_failed = (
        not report or
        "Research generation failed" in report or
        "# Error" in report or
        "Gemini Error" in report or
        "Groq Fallback Error" in report or
        "failed" in report.lower()[:100] or
        "temporarily unavailable" in report.lower() or
        "no report was generated" in report.lower()
    )
    if is_failed:
        return {
            "references_used": "N/A",
            "unique_sources": "N/A",
            "average_source_freshness": "N/A",
            "citation_density": "N/A",
            "evidence_coverage": "N/A",
            "evidence_panel": []
        }

    word_count = len(report.split()) if report else 0
    if word_count == 0:
        return {
            "references_used": 0,
            "unique_sources": 0,
            "average_source_freshness": "N/A",
            "citation_density": 0.0,
            "evidence_coverage": 0.0,
            "evidence_panel": []
        }
        
    citations = re.findall(r'\[(\d+)\]', report)
    citations_count = len(citations)
    
    citations_indices = set()
    for c in citations:
        idx = int(c)
        if 1 <= idx <= len(sources):
            citations_indices.add(idx)
            
    references_used = len(sources)
    unique_sources = len(sources)
    
    years = []
    for src in sources:
        if src.get("year"):
            try:
                years.append(int(src["year"]))
                continue
            except ValueError:
                pass
        url = src.get("url", "")
        url_years = re.findall(r'/20[0-2][0-9]/', url)
        if url_years:
            years.append(int(url_years[0].strip('/')))
            continue
        content = src.get("content", "") + " " + src.get("title", "")
        content_years = re.findall(r'\b(20[0-2][0-9])\b', content)
        if content_years:
            valid_years = [int(y) for y in content_years if int(y) <= current_year]
            if valid_years:
                years.append(max(valid_years))
                continue
        years.append(current_year)
        
    avg_year = sum(years) / len(years) if years else current_year
    avg_source_freshness = round(avg_year, 1)
    
    citation_density = round(citations_count / word_count, 4)
    
    # Extract body paragraphs properly:
    # Process lines sequentially. Ignore empty lines, headers, horizontal rules, and metadata fields.
    lines = report.split("\n")
    body_paragraphs = []
    current_para = []
    in_references = False
    
    for line in lines:
        line_strip = line.strip()
        if not line_strip:
            if current_para:
                body_paragraphs.append(" ".join(current_para))
                current_para = []
            continue
            
        if line_strip.startswith("## References") or line_strip.startswith("# References") or line_strip.startswith("## Academic Sources") or line_strip.startswith("# Academic Sources") or in_references:
            in_references = True
            if current_para:
                body_paragraphs.append(" ".join(current_para))
                current_para = []
            continue
            
        if (
            line_strip.startswith("#") 
            or line_strip.startswith("---") 
            or "Generated by ResearchPilot" in line_strip 
            or "Generated by Research Pilot" in line_strip 
            or "Archived by Poneglyph" in line_strip 
            or "Generated by Poneglyph" in line_strip 
            or "Poneglyph Intelligence" in line_strip
        ):
            if current_para:
                body_paragraphs.append(" ".join(current_para))
                current_para = []
            continue
            
        if line_strip.startswith("**Authors**:") or line_strip.startswith("**Year**:") or line_strip.startswith("**URL**:") or line_strip.startswith("**Link**:") or line_strip.startswith("**Topic**:"):
            if current_para:
                body_paragraphs.append(" ".join(current_para))
                current_para = []
            continue
            
        current_para.append(line_strip)
        
    if current_para:
        body_paragraphs.append(" ".join(current_para))
        
    # Filter out empty or too short paragraphs
    body_paragraphs = [bp for bp in body_paragraphs if len(bp) > 20]
    
    if body_paragraphs:
        paragraphs_with_citations = sum(1 for p in body_paragraphs if re.search(r'\[\d+\]', p))
        evidence_coverage = round(paragraphs_with_citations / len(body_paragraphs), 4)
    else:
        evidence_coverage = 0.0
        
    evidence_panel = []
    for idx in sorted(citations_indices):
        src = sources[idx - 1]
        title = src.get("title", "Unknown Source")
        url = src.get("url", "")
        content = src.get("raw_content") or src.get("content") or ""
        
        paragraphs = report.split("\n\n")
        context_sentences = []
        for p in paragraphs:
            if f"[{idx}]" in p:
                sentences = re.split(r'(?<=[.!?])\s+', p)
                for s in sentences:
                    if f"[{idx}]" in s:
                        context_sentences.append(s)
        context_text = " ".join(context_sentences)
        
        excerpt = ""
        source_sentences = []
        if content:
            source_sentences = re.split(r'(?<=[.!?])\s+', content)
            source_sentences = [s.strip() for s in source_sentences if len(s.strip()) > 15]
            
            context_words = set(re.findall(r'\w+', context_text.lower()))
            stopwords = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with", "is", "was", "were", "of", "that", "this", "these", "those"}
            context_keywords = context_words - stopwords
            
            # Score sentences
            sentence_scores = []
            for s in source_sentences:
                if not is_valid_evidence(s):
                    continue
                s_lower = s.lower()
                s_words = set(re.findall(r'\w+', s_lower)) - stopwords
                
                # Base score from keyword overlap with report context
                overlap = len(context_keywords.intersection(s_words))
                score = overlap * 2.0
                
                # Bonus for statistics/numbers/dates
                if re.search(r'\d+', s):
                    score += 1.5
                if re.search(r'[%$]', s) or re.search(r'\b(percent|million|billion|thousand)\b', s_lower):
                    score += 2.0
                
                # Bonus for findings, claims, metrics
                strong_keywords = {"found", "concluded", "stated", "reported", "according to", "metrics", "audience", "release", "research", "study", "analysis", "data", "evidence"}
                if strong_keywords.intersection(s_words):
                    score += 2.0
                    
                # Bonus for quotes
                if '"' in s or "“" in s or "”" in s or "'" in s:
                    score += 1.0
                    
                # Penalty for likely episode descriptions or boilerplate
                if re.search(r'\b(episode|season|chapter)\b', s_lower):
                    score -= 3.0
                if len(s_words) < 8:
                    score -= 2.0
                    
                sentence_scores.append((score, s))
            
            # Sort descending by score
            sentence_scores.sort(key=lambda x: x[0], reverse=True)
            
            for score, s in sentence_scores:
                if score >= 2.0:
                    excerpt = s
                    break
                    
        # If no excerpt found with overlap, search for any valid sentence in source_sentences
        if not excerpt and source_sentences:
            for s in source_sentences:
                if is_valid_evidence(s):
                    excerpt = s
                    break
            
        if len(excerpt) > 400:
            excerpt = excerpt[:400] + "..."
            
        if not excerpt:
            excerpt = "Evidence unavailable for this source."
            
        evidence_panel.append({
            "index": idx,
            "title": title,
            "url": url,
            "excerpt": excerpt
        })
        
    return {
        "references_used": references_used,
        "unique_sources": unique_sources,
        "average_source_freshness": avg_source_freshness,
        "citation_density": citation_density,
        "evidence_coverage": evidence_coverage,
        "evidence_panel": evidence_panel
    }

class ResearchState(TypedDict):
    query: str
    route: str
    bypass_ambiguity: bool
    domain: str
    
    needs_clarification: bool
    clarification_options: list

    search_results: list
    processed_sources: list

    rag_chunks: list
    rag_answer: str

    report: str

    critic_report: dict

    formatted_report: str

    insights: Dict[str, Any]

    sources: list
    activity_log: list

# -------------------------
# AMBIGUITY CHECK
# -------------------------

def ambiguity_node(state: ResearchState):
    print("AMBIGUITY NODE EXECUTED")
    
    if state.get("bypass_ambiguity", False) or len(state["query"].split()) > 3:
        return {
            "needs_clarification": False,
            "clarification_options": []
        }
    
    result = detect_ambiguity(state["query"])
    
    log = state.get("activity_log", []) + [{"agent": "Ambiguity Agent", "action": f"Checked query ambiguity. Needs clarification: {result.get('needs_clarification')}"}]
    
    return {
        "needs_clarification": result.get("needs_clarification", False),
        "clarification_options": result.get("options", []),
        "activity_log": log
    }

# -------------------------
# ROUTER
# -------------------------

def router_node(state: ResearchState):
    from agents.research_agent import classify_research_domain

    route = classify_query(
        state["query"]
    )
    
    domain = classify_research_domain(
        state["query"]
    )

    print(
        f"\nROUTE SELECTED: {route}\n"
        f"DOMAIN SELECTED: {domain}\n"
    )

    log = state.get("activity_log", []) + [
        {"agent": "Router Agent", "action": f"Classified query as {route}"},
        {"agent": "Router Agent", "action": f"Determined research domain as {domain}"}
    ]

    return {
        "route": route,
        "domain": domain,
        "activity_log": log
    }


def route_decision(state: ResearchState):

    route = state["route"]

    if route == "WEB":
        return "search"

    elif route == "RAG":
        return "rag"
    
    elif route == "HYBRID":
        return "hybrid"

    elif route == "ARXIV":
        return "arxiv"

    else:
        return "search"

def critic_node(state: ResearchState):
    print("CRITIC NODE EXECUTED")
    report = state.get("report", "")
    
    # Bypass Critic LLM call if the report failed
    is_failed = (
        not report or
        "Research generation failed" in report or
        "# Error" in report or
        "Gemini Error" in report or
        "Groq Fallback Error" in report or
        "failed" in report.lower()[:100] or
        "temporarily unavailable" in report.lower() or
        "no report was generated" in report.lower()
    )
    if is_failed:
        return {
            "critic_report": {
                "improved_report": report
            },
            "insights": {}
        }

    critic_result = review_report(
        query=state["query"],
        report=report
    )

    log = state.get("activity_log", []) + [{"agent": "Critic Agent", "action": "Reviewed report"}]

    return {
        "critic_report": critic_result,
        "insights": {},
        "activity_log": log
    }


# -------------------------
# WEB FLOW
# -------------------------

def search_node(state: ResearchState):
    print("SEARCH NODE EXECUTED")
    print("DIAGNOSTIC: Retrieval started")
    query = state["query"]

    try:
        results = search_web(query)
    except Exception as e:
        print(f"DIAGNOSTIC: Search web failed: {e}")
        results = []

    if len(results) < 5:
        from agents.search_agent import expand_queries
        print("Expanding queries to meet minimum source threshold...")
        try:
            expanded = expand_queries(query)
            seen_urls = {r.get("url") for r in results if r.get("url")}
            for q in expanded:
                if len(results) >= 6:
                    break
                if q.lower() == query.lower():
                    continue
                try:
                    more_results = search_web(q)
                    for mr in more_results:
                        url = mr.get("url")
                        if url and url not in seen_urls:
                            results.append(mr)
                            seen_urls.add(url)
                except Exception as e:
                    print(f"DIAGNOSTIC: Expanded search failed for '{q}': {e}")
        except Exception as e:
            print(f"DIAGNOSTIC: expand_queries failed: {e}")

    for r in results:
        r["priority"] = get_source_priority(r.get("url", ""), "web")
    results.sort(key=lambda x: x["priority"])

    sources = [
        {
            "title": result.get("title", result["url"]),
            "url": result["url"],
            "content": result.get("content", ""),
            "raw_content": result.get("raw_content", "")
        }
        for result in results[:8]
    ]
    
    print(f"DIAGNOSTIC: Retrieval completed")

    log = state.get("activity_log", []) + [{"agent": "Search Agent", "action": f"Retrieved {len(sources)} sources"}]

    return {
        "search_results": results,
        "sources": sources,
        "activity_log": log
    }


def reader_node(state: ResearchState):

    print("READER NODE EXECUTED")

    processed_sources = []

    for source in state["search_results"][:5]:

        processed_sources.append(
            summarize_source(source)
        )

    log = state.get("activity_log", []) + [{"agent": "Reader Agent", "action": f"Summarized {len(processed_sources)} sources"}]

    return {
        "processed_sources": processed_sources,
        "activity_log": log
    }


def research_node(state: ResearchState):

    print("RESEARCH NODE EXECUTED")

    report = generate_research_summary(
        query=state["query"],
        search_results=state["processed_sources"],
        route=state.get("route", "WEB")
    )

    log = state.get("activity_log", []) + [{"agent": "Research Agent", "action": "Generated draft report"}]

    return {
        "report": report,
        "activity_log": log
    }


GENERIC_STOCK_TERMS = [
    "earth", "planet", "globe", "space", "satellite", "galaxy", "universe",
    "technology background", "abstract technology", "digital world",
    "business background", "network background"
]

def calculate_relevance_score(image_metadata: dict, topic: str, generated_queries: list) -> float:
    score = 0.0
    
    stop_words = {"vs", "and", "or", "the", "a", "an", "of", "in", "on", "at", "for", "with", "about", "to", "from", "by", "over", "under", "analysis", "report", "overview"}
    def get_words(text):
        return {w.strip(".,()\"'?-:;") for w in text.lower().split() if w.strip(".,()\"'?-:;") and w.strip(".,()\"'?-:;") not in stop_words}
        
    metadata_title = image_metadata.get("source_title", "")
    metadata_context = image_metadata.get("source_context", "")
    metadata_url = image_metadata.get("url", "")
    metadata_text = (metadata_title + " " + metadata_context + " " + metadata_url).lower()
    metadata_words = get_words(metadata_text)
    
    # 1. Query Match (up to 30 points)
    img_query = image_metadata.get("query", "").lower()
    if any(img_query == gq.lower() for gq in generated_queries):
        score += 30.0
    else:
        gq_overlaps = []
        for gq in generated_queries:
            gq_words = get_words(gq)
            overlap = get_words(img_query) & gq_words
            if gq_words:
                gq_overlaps.append(len(overlap) / len(gq_words))
        if gq_overlaps:
            score += max(gq_overlaps) * 30.0
            
    # 2. Topic Match (up to 40 points)
    topic_words = get_words(topic)
    matches = 0
    for w in topic_words:
        if w in metadata_text:
            matches += 1
    if topic_words:
        score += (matches / len(topic_words)) * 40.0
    else:
        score += 40.0
        
    # 3. Semantic Similarity / Keyword Overlap (up to 30 points)
    all_query_words = set()
    for gq in generated_queries:
        all_query_words.update(get_words(gq))
    all_query_words.update(topic_words)
    
    overlap = all_query_words & metadata_words
    if all_query_words:
        score += (len(overlap) / min(len(all_query_words), 10)) * 30.0
        
    return min(100.0, max(0.0, score))

def calculate_entity_match_score(image_metadata: dict, topic: str) -> float:
    score = 0.0
    
    stop_words = {"vs", "and", "or", "the", "a", "an", "of", "in", "on", "at", "for", "with", "about", "to", "from", "by", "over", "under"}
    topic_words = [w.strip(".,()\"'?-:;") for w in topic.lower().split()]
    topic_entities = [w for w in topic_words if w and w not in stop_words and len(w) > 2]
    
    metadata_title = image_metadata.get("source_title", "")
    metadata_context = image_metadata.get("source_context", "")
    metadata_url = image_metadata.get("url", "")
    metadata_text = (metadata_title + " " + metadata_context + " " + metadata_url).lower()
    
    # 1. Primary entity check (+30)
    has_primary = any(entity in metadata_text for entity in topic_entities)
    if has_primary:
        score += 30.0
        
    # 2. Extra domain entity match (+20 per match)
    topic_lower = topic.lower()
    extra_entities = []
    if "openai" in topic_lower or "anthropic" in topic_lower or "claude" in topic_lower or "gpt" in topic_lower:
        extra_entities = ["openai", "anthropic", "claude", "gpt", "sam altman", "dario amodei", "sutskever", "mirati", "amodei", "altman", "transformer", "llm"]
    elif "wano" in topic_lower or "one piece" in topic_lower:
        extra_entities = ["wano", "one piece", "kaido", "luffy", "zoro", "alliance", "shogun", "samurai", "orochi", "momonosuke", "oden", "yamato", "straw hat", "anime", "manga"]
    elif "tesla" in topic_lower:
        extra_entities = ["tesla", "musk", "elon", "gigafactory", "tsla", "model 3", "model y", "cybertruck", "ev", "automotive", "investor", "financial"]
        
    for entity in extra_entities:
        if entity in metadata_text:
            score += 20.0
            
    return min(100.0, max(0.0, score))

def calculate_image_quality_score(image_metadata: dict, topic: str, base_quality_score: float) -> float:
    url = (image_metadata.get("source_url") or image_metadata.get("url") or "").lower()
    topic_lower = topic.lower()
    
    source_adj = 0.0
    
    # Preferred sources (+25)
    # AI
    if any(x in topic_lower for x in ["ai", "openai", "anthropic", "claude", "gpt", "deepmind", "neural", "intelligence"]):
        if any(d in url for d in ["openai.com", "anthropic.com", "datacamp.com", "huggingface.co"]):
            source_adj += 25.0
    # Anime / One Piece
    if any(x in topic_lower for x in ["wano", "one piece", "anime", "manga", "kaido", "luffy"]):
        if any(d in url for d in ["onepiece.fandom.com", "crunchyroll.com", "imdb.com"]):
            source_adj += 25.0
    # Finance
    if any(x in topic_lower for x in ["stock", "financial", "market", "tesla", "investing", "price"]):
        if any(d in url for d in ["investing.com", "yahoo.com", "stockanalysis.com", "cnn.com"]):
            source_adj += 25.0
            
    # Penalties:
    # stock photo sites (-40)
    stock_sites = ["shutterstock.com", "gettyimages.com", "alamy.com", "dreamstime.com", "123rf.com", "istockphoto.com", "depositphotos.com", "adobe.com/products/stock", "vectorstock.com", "freepik.com", "unsplash.com", "pixabay.com", "pexels.com"]
    if any(d in url for d in stock_sites):
        source_adj -= 40.0
        
    # generic blogs (-15)
    blog_sites = ["blogspot.com", "wordpress.com", "medium.com", "tumblr.com"]
    if any(d in url for d in blog_sites):
        source_adj -= 15.0
        
    # wallpaper sites (-30)
    wallpaper_sites = ["wallpaperflare.com", "wallpapersden.com", "hdwallpapers.in", "wallpaperaccess.com", "wallpapercave.com"]
    if any(d in url for d in wallpaper_sites):
        source_adj -= 30.0
        
    return min(100.0, max(0.0, base_quality_score + source_adj))

def search_serper_images(query: str) -> dict:
    import requests
    import os
    serper_api_key = os.getenv("SERPER_API_KEY")
    if not serper_api_key:
        print("Warning: SERPER_API_KEY not found in environment variables.")
        return {}
    
    url = "https://google.serper.dev/images"
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
        images_data = response.json().get("images", [])
        
        results = []
        images = []
        for img in images_data:
            img_url = img.get("imageUrl")
            if img_url:
                images.append(img_url)
                results.append({
                    "url": img.get("link", "Unknown"),
                    "title": img.get("title", "Image Search Result"),
                    "content": "Found directly via Serper image search query.",
                    "images": [img_url]
                })
        return {
            "results": results,
            "images": images
        }
    except Exception as e:
        print(f"Serper image search failed: {e}")
        return {}


VISUAL_CONTENT_KEYWORDS = [
    "character", "battle", "fight", "scene", "artwork", "illustration", "poster",
    "cover", "fortress", "anime", "manga", "official art", "key visual", "portrait",
    "hero image", "concept art", "screenshot"
]

LOW_VALUE_KEYWORDS = [
    "timeline", "diagram", "map", "flowchart", "graph", "schema", "table",
    "navigation", "infographic", "spreadsheet", "chart", "network", "topology"
]

def calculate_visual_value_score(image_metadata: dict) -> float:
    score = 50.0
    
    metadata_text = (
        image_metadata.get("source_title", "") + " " + 
        image_metadata.get("source_context", "") + " " + 
        image_metadata.get("query", "") + " " +
        image_metadata.get("url", "")
    ).lower()
    
    # 1. ADD VISUAL VALUE BOOSTS (+30)
    has_boost = False
    for kw in VISUAL_CONTENT_KEYWORDS:
        if kw in metadata_text:
            has_boost = True
            break
    if has_boost:
        score += 30.0
        
    # 2. ADD DIAGRAM PENALTIES (-40)
    has_penalty = False
    for kw in LOW_VALUE_KEYWORDS:
        if kw in metadata_text:
            has_penalty = True
            break
    if has_penalty:
        score -= 40.0
        
    return min(100.0, max(0.0, score))

def validate_image_url(url: str) -> bool:
    url_lower = url.lower()
    
    # 3. Reject images with placeholder keywords in URL/filename
    for placeholder in ["placeholder", "no-image", "default", "missing", "blank"]:
        if placeholder in url_lower:
            print(f"Image validation rejected: URL contains placeholder '{placeholder}' - {url}")
            return False
            
    import requests
    from PIL import Image
    from io import BytesIO
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    # HEAD request validation (Option A)
    try:
        head_resp = requests.head(url, headers=headers, timeout=3, allow_redirects=True)
        if head_resp.status_code != 200:
            print(f"Image validation rejected: HEAD status code {head_resp.status_code} - {url}")
            return False
    except Exception as e:
        print(f"Image validation: HEAD request failed: {e} - trying GET directly")
        
    # GET request validation and dimensions check (Option B)
    try:
        resp = requests.get(url, headers=headers, timeout=5, allow_redirects=True)
        if resp.status_code != 200:
            print(f"Image validation rejected: GET status code {resp.status_code} - {url}")
            return False
            
        img = Image.open(BytesIO(resp.content))
        width, height = img.size
        # Reject images when width < 400 or height < 300
        if width < 400 or height < 300:
            print(f"Image validation rejected: dimensions {width}x{height} are less than 400x300 - {url}")
            return False
            
        return True
    except Exception as e:
        print(f"Image validation rejected: Failed to download or open with PIL: {e} - {url}")
        return False


def contains_topic_keywords(image_metadata: dict, topic: str) -> bool:
    stop_words = {"vs", "and", "or", "the", "a", "an", "of", "in", "on", "at", "for", "with", "about", "to", "from", "by", "over", "under", "report", "analysis", "overview"}
    topic_words = [w.strip(".,()\"'?-:;") for w in topic.lower().split()]
    topic_keywords = [w for w in topic_words if w and w not in stop_words and len(w) > 2]
    if not topic_keywords:
        return True
    
    title = (image_metadata.get("source_title") or "").lower()
    url = (image_metadata.get("url") or "").lower()
    query = (image_metadata.get("query") or "").lower()
    
    text_to_check = title + " " + url + " " + query
    return any(kw in text_to_check for kw in topic_keywords)


def is_generic_or_earth_fallback(image_metadata: dict, topic: str) -> bool:
    space_keywords = ["astronomy", "space", "earth observation", "planet", "globe", "satellite", "nasa", "spacex", "galaxy", "universe", "mars", "moon", "solar system", "orbit", "cosmos", "climate change", "geography"]
    if any(k in topic.lower() for k in space_keywords):
        return False
        
    url = (image_metadata.get("url") or "").lower()
    title = (image_metadata.get("source_title") or "").lower()
    context = (image_metadata.get("source_context") or "").lower()
    query = (image_metadata.get("query") or "").lower()
    
    blacklist = [
        "earth", "planet", "globe", "space", "satellite", "galaxy", "universe",
        "technology background", "abstract technology", "digital world",
        "business background", "network background", "stockphoto", "stock-photo",
        "stockimage", "stock-image", "gettyimage", "shutterstock", "dreamstime", "istockphoto"
    ]
    
    for term in blacklist:
        if term in url or term in title or term in context or term in query:
            return True
    return False


def is_valid_candidate(cand: dict, topic: str, queries: list) -> bool:
    # 1. Similarity checks (Threshold: gemini_relevance >= 70, python relevance >= 60)
    rel_val = float(cand.get("gemini_relevance_score", 0))
    python_rel = float(cand.get("relevance_score", 0))
    if rel_val < 70 or python_rel < 60:
        return False
        
    # 2. Topic keyword check in title/url
    if not contains_topic_keywords(cand, topic):
        return False
        
    # 3. Generic stock / Earth-from-space check
    if is_generic_or_earth_fallback(cand, topic):
        return False
        
    return True


def classify_topic_category(topic: str) -> str:
    category_prompt = f"""
Classify the research topic: "{topic}" into exactly one of the following content categories:
- Character (biographies, specific fictional characters, historical people, authors, executives, figures, e.g. Darth Vader, Optimus Prime)
- Comparison (versus topics, comparison between two things, strategic comparisons, e.g. Apple vs Android, OpenAI vs Anthropic, Messi vs Ronaldo, Naruto vs Sasuke)
- Company/Product (brands, organizations, softwares, models, hardware, specific products, companies)
- Technology (algorithms, architectures, scientific domains, technical frameworks, computing standards, e.g. Quantum Computing)
- Event (wars, battles, incidents, timelines, historical events, conferences, e.g. Wano Arc, Marineford)
- Location (countries, islands, fortresses, buildings, maps, geographical areas)
- Historical Topic (eras, historical trends, ancient civilizations, archaeological periods, e.g. French Revolution)
- Sports/Athlete (sports, athletes, players, tournaments, sports history)
- Concept (philosophies, ideas, literary themes, abstract paradigms)

Return only the category name from the list. Do not include any punctuation, quotes, or explanation.
"""
    try:
        from llm.gemini_client import generate
        category = generate(category_prompt).strip()
    except Exception:
        try:
            from llm.groq_client import generate as groq_generate
            category = groq_generate(category_prompt).strip()
        except Exception:
            topic_lower = topic.lower()
            if any(x in topic_lower for x in [" vs ", " versus ", "compare", "comparison"]):
                category = "Comparison"
            elif any(x in topic_lower for x in ["athlete", "sport", "player", "tournament", "football", "soccer", "basketball", "tennis"]):
                category = "Sports/Athlete"
            elif any(x in topic_lower for x in ["how to", "concept", "theory", "philosophy"]):
                category = "Concept"
            elif any(x in topic_lower for x in ["history", "ancient", "era", "century", "revolution"]):
                category = "Historical Topic"
            elif any(x in topic_lower for x in ["software", "system", "architecture", "algorithm", "network", "computing"]):
                category = "Technology"
            else:
                category = "Concept"

    category_map = {
        "character": "Character",
        "comparison": "Comparison",
        "company/product": "Company/Product",
        "company": "Company/Product",
        "product": "Company/Product",
        "technology": "Technology",
        "event": "Event",
        "location": "Location",
        "historical topic": "Historical Topic",
        "historical": "Historical Topic",
        "sports/athlete": "Sports/Athlete",
        "sports": "Sports/Athlete",
        "athlete": "Sports/Athlete",
        "concept": "Concept"
    }
    
    category_cleaned = category.lower().replace("-", "").replace("*", "").strip()
    for key, val in category_map.items():
        if key in category_cleaned:
            return val
    return "Concept"


def get_image_diagnostics(topic: str) -> dict:
    category = classify_topic_category(topic)
    candidates = []
    queries = []
    selected_images = []
    results_found_count = 0
    top_match_score = 0.0
    fallback_used = False
    
    try:
        from llm.gemini_client import generate
        from tavily import TavilyClient
        import os
        import json
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        # 1. Generate 5 visual queries based on classified category
        query_generation_prompt = f"""
We are generating a research report on the topic: "{topic}".
This topic has been classified as category: "{category}".

Based on this category, we use the following retrieval strategy:
- Character: Generate queries for character artwork, official portraits, executive photos, anime/game design sheet, and close-ups. (e.g. "Optimus Prime official artwork")
- Comparison: Generate queries for comparison charts, strategic matrices, vs tables, feature checklists, and market share bar graphs. (e.g. "OpenAI vs Anthropic infographic", "Messi vs Ronaldo comparison")
- Company/Product: Generate queries for company logos, product comparison tables, hardware/software infographics, office buildings, or model architecture diagrams.
- Technology: Generate queries for system architecture diagrams, flowcharts, code structure visualizations, performance benchmark charts, or technical schematics. (e.g. "Apple vs Android comparison graphic")
- Event: Generate queries for historical battle maps, scene illustrations, timeline infographics, key incident diagrams, or official event posters. (e.g. "Marineford Arc key visual")
- Location: Generate queries for regional maps, fortress layouts, building photographs, satellite/aerial maps, or landscape illustrations.
- Historical Topic: Generate queries for historical artifacts, ancient maps, chronological timelines, archival photographs, or historical period illustrations. (e.g. "French Revolution timeline")
- Sports/Athlete: Generate queries for athlete action shots, professional portraits, team logos, stadium photographs, or performance comparison statistics.
- Concept: Generate queries for conceptual mind maps, philosophical diagrams, abstract flowcharts, themed infographics, or symbolism illustrations.

Generate exactly 5 distinct, topic-specific visual search queries optimized for search engines to find relevant images (such as charts, diagrams, infographics, maps, logos, or portraits) for this report.

Follow these rules:
1. Make them highly specific to the actual entities, sub-topics, characters, or companies in "{topic}".
2. Do not use generic categories (like "person", "concept", "timeline", "landmark", "overview") as prefixes or labels.
3. Incorporate visual modifier words (such as "comparison chart", "infographic", "illustration", "map", "market share", "portrait", "diagram") naturally.
4. Do not include category labels or formatting. Output exactly 5 lines, one query per line.
"""
        try:
            response = generate(query_generation_prompt).strip()
        except Exception as gemini_err:
            import logging
            logging.getLogger(__name__).warning("fetch_report_images (query generation): Gemini call failed. Activating Groq fallback.", exc_info=True)
            from llm.groq_client import generate as groq_generate
            response = groq_generate(query_generation_prompt).strip()

        queries = [q.strip() for q in response.split("\n") if q.strip()]
        queries = [q for q in queries if len(q) < 100]
        if not queries:
            queries = [topic]
            
        # 2. Retrieve candidate images along with search result context in parallel
        client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        seen_urls = set()
        
        def run_single_search(q):
            try:
                res = client.search(query=q, include_images=True)
                return q, res, False
            except Exception as e:
                print("Tavily image search failed, switching to Serper")
                try:
                    res_serper = search_serper_images(q)
                    return q, res_serper, True
                except Exception as se:
                    print(f"Serper image search failed: {se}")
                    return q, {}, False

        futures = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            for query in queries[:5]:
                futures.append(executor.submit(run_single_search, query))
                
        raw_candidates = []
        for fut in as_completed(futures):
            query, res, is_serper = fut.result()
            results = res.get("results", []) if res else []
            
            # First, collect images associated with specific results (with context)
            for r in results:
                img_list = r.get("images", [])
                for img in img_list:
                    if img and img.startswith("http") and img not in seen_urls:
                        seen_urls.add(img)
                        raw_candidates.append({
                            "url": img,
                            "query": query,
                            "source_url": r.get("url"),
                            "source_title": r.get("title", "Unknown Source"),
                            "source_context": r.get("content", "")[:250]
                        })
            
            # Second, collect any remaining general images that didn't map to a specific result
            general_imgs = res.get("images", []) if res else []
            for img in general_imgs:
                if img and img.startswith("http") and img not in seen_urls:
                    seen_urls.add(img)
                    raw_candidates.append({
                        "url": img,
                        "query": query,
                        "source_url": "Unknown",
                        "source_title": "Image Search Result",
                        "source_context": "Found directly via image search query."
                    })

        # Apply relevance validation checks (keyword match, stock photo filter)
        filtered_candidates = []
        for c in raw_candidates:
            # Check if it has generic or earth-from-space fallback terms
            if is_generic_or_earth_fallback(c, topic):
                continue
            # Check if title or url contains topic keywords
            if not contains_topic_keywords(c, topic):
                continue
            filtered_candidates.append(c)
            
        candidates = filtered_candidates
        results_found_count = len(candidates)
        
        # Limit to top 12 candidates for scoring
        candidates = candidates[:12]
        if candidates:
            # 3. Score candidate images via Gemini using context metadata
            scoring_prompt = f"""
We are generating a research report on the topic: "{topic}".
We have retrieved the following candidate images along with their search queries, source titles, source URLs, and context snippets.

Your task is to:
1. Classify each candidate image into EXACTLY ONE of the following categories based on its metadata and context:
   - character: Character artwork, portraits, specific figures, close-up drawings or photos of key people.
   - scene: Battle scenes, fight scenes, action drawings, anime/movie screenshots, action setups.
   - artwork: Official artwork, posters, covers, landmarks, fortresses, buildings, company offices, product/location photos.
   - diagram: Timeline, diagram, flowchart, map, infographic, graph, schema, table.

2. Evaluate each image metadata and provide three semantic scores on a scale from 0 to 100:
   - gemini_relevance_score: How closely the image's source page topic and context snippet align with the overall report topic "{topic}" and the specific query.
   - gemini_entity_score: How well the image depicts the key named entities (people, products, models, companies) related to the topic "{topic}".
   - gemini_quality_score: The estimated visual quality and utility of the image for the report.

Candidate Images:
{json.dumps(candidates, indent=2)}

Return the results as a JSON array of objects, containing ONLY the "url", "category", "gemini_relevance_score", "gemini_entity_score", "gemini_quality_score", and a brief "reason".
Return ONLY valid JSON:
[
  {{
    "url": "...",
    "category": "character" | "scene" | "artwork" | "diagram",
    "gemini_relevance_score": 85,
    "gemini_entity_score": 90,
    "gemini_quality_score": 80,
    "reason": "..."
  }},
  ...
]
"""
            try:
                scoring_resp = generate(scoring_prompt).strip()
            except Exception as gemini_err:
                import logging
                logging.getLogger(__name__).warning("fetch_report_images (scoring): Gemini call failed. Activating Groq fallback.", exc_info=True)
                from llm.groq_client import generate as groq_generate
                scoring_resp = groq_generate(scoring_prompt).strip()

            start = scoring_resp.find("[")
            end = scoring_resp.rfind("]")
            if start != -1 and end != -1 and end > start:
                parsed = json.loads(scoring_resp[start:end+1])
                allowed_categories = {'character', 'scene', 'artwork', 'diagram'}
                
                for img in parsed:
                    url = img.get("url")
                    cand = next((c for c in candidates if c["url"] == url), None)
                    if not cand:
                        continue
                    
                    cat = img.get("category", "diagram").lower().strip()
                    if cat not in allowed_categories:
                        if 'char' in cat or 'portrait' in cat or 'person' in cat or 'avatar' in cat:
                            cat = 'character'
                        elif 'scene' in cat or 'battle' in cat or 'fight' in cat or 'screenshot' in cat:
                            cat = 'scene'
                        elif 'art' in cat or 'poster' in cat or 'cover' in cat or 'landmark' in cat or 'fort' in cat:
                            cat = 'artwork'
                        else:
                            cat = 'diagram'
                    cand["category"] = cat
                    
                    try:
                        gemini_rel = float(img.get("gemini_relevance_score", 50.0))
                    except:
                        gemini_rel = 50.0
                    try:
                        gemini_ent = float(img.get("gemini_entity_score", 50.0))
                    except:
                        gemini_ent = 50.0
                    try:
                        gemini_qual = float(img.get("gemini_quality_score", 50.0))
                    except:
                        gemini_qual = 50.0
                    
                    relevance_score = (gemini_rel + calculate_relevance_score(cand, topic, queries)) / 2.0
                    entity_match_score = (gemini_ent + calculate_entity_match_score(cand, topic)) / 2.0
                    image_quality_score = calculate_image_quality_score(cand, topic, gemini_qual)
                    visual_value_score = calculate_visual_value_score(cand)
                    
                    final_score = (
                        relevance_score * 0.50 +
                        entity_match_score * 0.20 +
                        visual_value_score * 0.20 +
                        image_quality_score * 0.10
                    )
                    
                    cand["relevance_score"] = relevance_score
                    cand["entity_match_score"] = entity_match_score
                    cand["image_quality_score"] = image_quality_score
                    cand["visual_value_score"] = visual_value_score
                    cand["final_score"] = final_score
                    cand["gemini_relevance_score"] = gemini_rel
                    cand["gemini_entity_score"] = gemini_ent

                # Filter scored candidates using strict validation rules
                scored_candidates = [c for c in candidates if "final_score" in c]
                valid_scored_candidates = []
                for c in scored_candidates:
                    if is_valid_candidate(c, topic, queries):
                        if validate_image_url(c["url"]):
                            valid_scored_candidates.append(c)
                
                if valid_scored_candidates:
                    valid_scored_candidates = sorted(valid_scored_candidates, key=lambda x: x["final_score"], reverse=True)
                    hero = valid_scored_candidates[0]
                    selected_candidates = [hero]
                    selected_urls = [hero["url"]]
                    selected_categories = {hero["category"]}

                    # Try to pick 1 character image
                    if "character" not in selected_categories:
                        for c in valid_scored_candidates[1:]:
                            if c["category"] == "character" and c["url"] not in selected_urls:
                                selected_candidates.append(c)
                                selected_urls.append(c["url"])
                                selected_categories.add("character")
                                break
                                
                    # Try to pick 1 scene/battle image
                    if len(selected_urls) < 3 and "scene" not in selected_categories:
                        for c in valid_scored_candidates[1:]:
                            if c["category"] == "scene" and c["url"] not in selected_urls:
                                selected_candidates.append(c)
                                selected_urls.append(c["url"])
                                selected_categories.add("scene")
                                break
                                
                    # Try to pick 1 artwork image
                    if len(selected_urls) < 3 and "artwork" not in selected_categories:
                        for c in valid_scored_candidates[1:]:
                            if c["category"] == "artwork" and c["url"] not in selected_urls:
                                selected_candidates.append(c)
                                selected_urls.append(c["url"])
                                selected_categories.add("artwork")
                                break
                                
                    # Fill with any non-diagram images
                    if len(selected_urls) < 3:
                        for c in valid_scored_candidates[1:]:
                            if c["url"] not in selected_urls and c["category"] != "diagram":
                                selected_candidates.append(c)
                                selected_urls.append(c["url"])
                                selected_categories.add(c["category"])
                                if len(selected_urls) == 3:
                                    break
                                    
                    # Fallback to allow diagram images as last resort (Max 1 diagram total)
                    if len(selected_urls) < 3:
                        for c in valid_scored_candidates[1:]:
                            if c["url"] not in selected_urls:
                                diagram_count = sum(1 for x in selected_candidates if x["category"] == "diagram")
                                if c["category"] == "diagram" and diagram_count >= 1:
                                    continue
                                selected_candidates.append(c)
                                selected_urls.append(c["url"])
                                if len(selected_urls) == 3:
                                    break

                    selected_candidates.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
                    selected_images = [c["url"] for c in selected_candidates]
                    top_match_score = selected_candidates[0]["final_score"]

    except Exception as e:
        print(f"Failed to fetch and score report images: {e}")

    return {
        "topic": topic,
        "category": category,
        "queries": queries,
        "results_found": results_found_count,
        "candidates": candidates,
        "selected_images": selected_images,
        "top_match_score": top_match_score,
        "fallback_used": fallback_used
    }


def fetch_report_images(topic: str) -> list:
    diag = get_image_diagnostics(topic)
    category = diag["category"]
    queries = diag["queries"]
    results_found_count = diag["results_found"]
    selected_images = diag["selected_images"]
    top_match_score = diag["top_match_score"]
    fallback_used = diag["fallback_used"]
    
    print(f"TOPIC: {topic}")
    print(f"CATEGORY: {category}")
    for q in queries:
        print(f"IMAGE_QUERY: {q}")
    print(f"RESULTS_FOUND: {results_found_count}")
    print(f"TOP_MATCH_SCORE: {top_match_score}")
    
    if selected_images:
        print(f"SELECTED_IMAGE: {selected_images[0]}")
    else:
        print("SELECTED_IMAGE: None")
        
    print(f"FALLBACK_USED: {fallback_used}")
    
    # Selection diagnostics console trace
    print("--- IMAGE SELECTION DIAGNOSTICS ---")
    if selected_images:
        print(f"Successfully selected {len(selected_images)} images. Hero: {selected_images[0]}")
        print(f"Top Match Final Score: {top_match_score}")
    else:
        print("No images passed validation and scoring thresholds. Return NO HERO IMAGE.")
    print("-----------------------------------")
    
    return selected_images


def writer_node(state: ResearchState):
    print("WRITER NODE EXECUTED")
    critic_data = state.get("critic_report")
    report_to_format = state["report"]

    is_failed = (
        not report_to_format or
        "temporarily unavailable" in report_to_format.lower() or
        "no report was generated" in report_to_format.lower() or
        "failed" in report_to_format.lower()[:100]
    )
    
    images = []
    if not is_failed:
        images = fetch_report_images(state["query"])

    formatted_report = format_report(
        report=report_to_format,
        query=state["query"],
        sources=state["sources"],
        images=images,
        route=state.get("route", "WEB")
    )

    # Calculate Research Quality Indicators
    metrics = calculate_quality_metrics(formatted_report, state.get("sources", []))
    
    insights = state.get("insights", {})
    insights["word_count"] = len(report_to_format.split())
    insights["reference_count"] = metrics["references_used"]
    insights["references_used"] = metrics["references_used"]
    insights["unique_sources"] = metrics["unique_sources"]
    insights["average_source_freshness"] = metrics["average_source_freshness"]
    insights["citation_density"] = metrics["citation_density"]
    insights["evidence_coverage"] = metrics["evidence_coverage"]
    insights["evidence_panel"] = metrics["evidence_panel"]
    
    hero_image = images[0] if images else None
    insights["hero_image"] = hero_image
    insights["images"] = images
    insights["domain"] = state.get("domain", "General Research")

    if not is_failed:
        save_research(
            query=state["query"],
            route=state["route"],
            report=formatted_report,
            sources=state.get("sources", []),
            insights=insights,
            hero_image=hero_image
        )

    log = state.get("activity_log", []) + [{"agent": "Writer Agent", "action": "Generated final formatted report"}]

    return {
        "formatted_report": formatted_report,
        "insights": insights,
        "activity_log": log
    }

# -------------------------
# RAG FLOW
# -------------------------

def rag_node(state: ResearchState):
    from rag.retriever import retrieve
    from agents.rag_answer_agent import generate_rag_answer

    chunks = retrieve(
        state["query"]
    )

    answer = generate_rag_answer(
        state["query"],
        chunks
    )

    log = state.get("activity_log", []) + [{"agent": "RAG Agent", "action": f"Retrieved {len(chunks)} chunks & generated answer"}]

    return {
        "rag_chunks": chunks,
        "rag_answer": answer,
        "activity_log": log
    }


def rag_writer_node(state: ResearchState):

    formatted_report = format_report(
        report=state["rag_answer"],
        query=state["query"],
        sources=[],
        route="RAG"
    )

    insights = {
        "word_count": len(state["rag_answer"].split()),
        "reference_count": 0,
        "references_used": 0,
        "unique_sources": 0,
        "average_source_freshness": "N/A",
        "citation_density": 0.0,
        "evidence_coverage": 0.0,
        "evidence_panel": [],
        "domain": state.get("domain", "General Research")
    }

    is_failed = (
        not state["rag_answer"] or
        "failed" in state["rag_answer"].lower()[:100] or
        "temporarily unavailable" in state["rag_answer"].lower()
    )
    if not is_failed:
        save_research(
            query=state["query"],
            route="RAG",
            report=formatted_report,
            sources=[],
            insights=insights
        )

    log = state.get("activity_log", []) + [{"agent": "Writer Agent", "action": "Generated final formatted report"}]

    return {
        "formatted_report": formatted_report,
        "insights": insights,
        "activity_log": log
    }



def hybrid_node(state: ResearchState):
    from rag.retriever import retrieve

    web_results = search_web(
        state["query"]
    )

    rag_chunks = retrieve(
        state["query"]
    )

    combined_results = []
    sources_list = []

    # web results

    for result in web_results[:5]:
        item = {
            "title": result["title"],
            "url": result["url"],
            "content": result.get("content", ""),
            "raw_content": result.get("raw_content", "")
        }
        combined_results.append(item)
        sources_list.append(item)

    # rag results

    for idx, chunk in enumerate(rag_chunks, start=1):
        item = {
            "title": f"Local Knowledge Base (Chunk {idx})",
            "url": "RAG",
            "content": chunk,
            "raw_content": chunk
        }
        combined_results.append(item)
        sources_list.append(item)

    route = "HYBRID"
    if not rag_chunks:
        route = "WEB"

    log = state.get("activity_log", []) + [{"agent": "Hybrid Agent", "action": f"Combined {len(web_results[:5])} web sources and {len(rag_chunks)} local chunks"}]

    return {
        "processed_sources": combined_results,
        "sources": sources_list,
        "route": route,
        "activity_log": log
    }


# -------------------------
# ARXIV FLOW
# -------------------------

def arxiv_node(state: ResearchState):
    print("ARXIV NODE EXECUTED")
    print("DIAGNOSTIC: Retrieval started")
    from services.arxiv_service import search_arxiv
    query = state["query"]
    
    try:
        results = search_arxiv(query, max_results=10)
    except Exception as e:
        print(f"arXiv search failed: {e}. Falling back to WEB route.")
        results = []

    if len(results) < 5:
        from agents.arxiv_agent import expand_academic_queries
        print("Expanding queries to meet minimum source threshold for arXiv...")
        try:
            expanded = expand_academic_queries(query)
            seen_urls = {r.get("arxiv_url") for r in results if r.get("arxiv_url")}
            for q in expanded:
                if len(results) >= 6:
                    break
                if q.lower() == query.lower():
                    continue
                try:
                    more_results = search_arxiv(q, max_results=10)
                    for mr in more_results:
                        url = mr.get("arxiv_url")
                        if url and url not in seen_urls:
                            results.append(mr)
                            seen_urls.add(url)
                except Exception as e:
                    print(f"Expanded arXiv search failed for '{q}': {e}")
        except Exception as e:
            print(f"expand_academic_queries failed: {e}")

    if not results:
        # Fall back to WEB route
        log = state.get("activity_log", []) + [{"agent": "arXiv Agent", "action": "No arXiv papers found. Falling back to WEB route."}]
        return {
            "route": "WEB",
            "activity_log": log
        }

    for r in results:
        r["priority"] = get_source_priority(r.get("arxiv_url", ""), "arxiv")
    results.sort(key=lambda x: x["priority"])

    sources = []
    processed_sources = []
    for paper in results[:8]:
        published_val = paper.get("published_date") or paper.get("published") or ""
        year = published_val[:4] if published_val else "Unknown"
        
        authors_val = paper.get("authors")
        if isinstance(authors_val, list):
            authors_str = ", ".join(authors_val)
        else:
            authors_str = str(authors_val) if authors_val else "Unknown"
            
        item = {
            "title": paper.get("title", "Unknown Title"),
            "url": paper.get("arxiv_url") or paper.get("pdf_url") or "",
            "pdf_url": paper.get("pdf_url") or "",
            "authors": authors_str,
            "year": year,
            "content": paper.get("summary", ""),
            "raw_content": paper.get("summary", ""),
            "source_type": "arxiv"
        }
        sources.append(item)
        processed_sources.append(item)
        
    print(f"DIAGNOSTIC: Retrieval completed")

    log = state.get("activity_log", []) + [{"agent": "arXiv Agent", "action": f"Retrieved {len(sources)} academic papers"}]

    return {
        "sources": sources,
        "processed_sources": processed_sources,
        "activity_log": log
    }


def arxiv_decision(state: ResearchState):
    if state["route"] == "WEB":
        return "search"
    return "research"

# -------------------------
# GRAPH
# -------------------------

builder = StateGraph(
    ResearchState
)

builder.add_node(
    "router",
    router_node
)

builder.add_node(
    "search",
    search_node
)

builder.add_node(
    "reader",
    reader_node
)

builder.add_node(
    "research",
    research_node
)

builder.add_node(
    "writer",
    writer_node
)

builder.add_node(
    "rag",
    rag_node
)

builder.add_node(
    "rag_writer",
    rag_writer_node
)

builder.add_node(
    "hybrid",
    hybrid_node
)

builder.add_node(
    "critic",
    critic_node
)

builder.add_node(
    "ambiguity",
    ambiguity_node
)

builder.add_node(
    "arxiv",
    arxiv_node
)

builder.set_entry_point(
    "ambiguity"
)

def ambiguity_decision(state: ResearchState):
    if state.get("needs_clarification", False):
        return "end"
    return "router"

builder.add_conditional_edges(
    "ambiguity",
    ambiguity_decision,
    {
        "end": END,
        "router": "router"
    }
)

builder.add_conditional_edges(
    "router",
    route_decision,
    {
        "search": "search",
        "rag": "rag",
        "hybrid": "hybrid",
        "arxiv": "arxiv"
    }
)

builder.add_conditional_edges(
    "arxiv",
    arxiv_decision,
    {
        "search": "search",
        "research": "research"
    }
)

# WEB PATH

builder.add_edge(
    "search",
    "reader"
)

builder.add_edge(
    "reader",
    "research"
)

# RAG PATH

builder.add_edge(
    "rag",
    "rag_writer"
)

builder.add_edge(
    "rag_writer",
    END
)

builder.add_edge(
    "hybrid",
    "research"
)


builder.add_edge(
    "research",
    "critic"
)

builder.add_edge(
    "critic",
    "writer"
)

builder.add_edge(
    "writer",
    END
)

graph = builder.compile()