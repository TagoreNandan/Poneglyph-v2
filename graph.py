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

from rag.retriever import retrieve
from agents.rag_answer_agent import generate_rag_answer

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
            
        if line_strip.startswith("## References") or line_strip.startswith("# References") or in_references:
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

    route = classify_query(
        state["query"]
    )

    print(
        f"\nROUTE SELECTED: {route}\n"
    )

    log = state.get("activity_log", []) + [{"agent": "Router Agent", "action": f"Classified query as {route}"}]

    return {
        "route": route,
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


def fetch_report_images(topic: str) -> list:
    print(f"Fetching images for topic: {topic}")
    candidates = []
    try:
        from llm.gemini_client import generate
        from tavily import TavilyClient
        import os
        import json
        
        # 1. Generate 5 visual queries based on categories
        query_generation_prompt = f"""
Given the research topic: "{topic}", generate exactly 5 distinct search queries optimized for search engines to find high-quality, relevant images for a research report.
You must generate exactly one query for each of the following categories:
1. person: A key historical figure or person related to the topic (e.g. "Linus Torvalds portrait" for Linux).
2. concept: A technical concept diagram, architecture, or model representation (e.g. "Linux kernel architecture diagram").
3. timeline: A timeline, history infographic, or evolutionary chart (e.g. "Linux history timeline").
4. landmark: A visual landmark, emblem, famous mascot, or key artifact (e.g. "Tux penguin mascot Linux logo").
5. overview: A general historical photograph, high-level overview, or key setup (e.g. "early computer running Linux history").

Do not include category labels or formatting. Output exactly 5 lines, one query per line.
"""
        response = generate(query_generation_prompt).strip()
        queries = [q.strip() for q in response.split("\n") if q.strip()]
        queries = [q for q in queries if len(q) < 100]
        if not queries:
            queries = [topic]
            
        print(f"Generated image search queries: {queries}")
        
        # 2. Retrieve candidate images along with search result context in parallel
        client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        seen_urls = set()
        
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        def run_single_search(q):
            try:
                res = client.search(query=q, include_images=True)
                return q, res
            except Exception as e:
                print(f"Error fetching image for query '{q}': {e}")
                return q, {}

        futures = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            for query in queries[:5]:
                futures.append(executor.submit(run_single_search, query))
                
        for fut in as_completed(futures):
            query, res = fut.result()
            results = res.get("results", [])
            print(f"Tavily image search for '{query}' returned {len(results)} search results")
            
            # First, collect images associated with specific results (with context)
            for r in results:
                img_list = r.get("images", [])
                for img in img_list:
                    if img and img.startswith("http") and img not in seen_urls:
                        seen_urls.add(img)
                        candidates.append({
                            "url": img,
                            "query": query,
                            "source_url": r.get("url"),
                            "source_title": r.get("title", "Unknown Source"),
                            "source_context": r.get("content", "")[:250]
                        })
            
            # Second, collect any remaining general images that didn't map to a specific result
            general_imgs = res.get("images", [])
            for img in general_imgs:
                if img and img.startswith("http") and img not in seen_urls:
                    seen_urls.add(img)
                    candidates.append({
                        "url": img,
                        "query": query,
                        "source_url": "Unknown",
                        "source_title": "Image Search Result",
                        "source_context": "Found directly via image search query."
                    })
                
        # Limit to top 12 candidates for scoring
        candidates = candidates[:12]
        if not candidates:
            return []
            
        # 3. Score and deduplicate candidate images via Gemini using context metadata
        scoring_prompt = f"""
We are generating a research report on the topic: "{topic}".
We have retrieved the following candidate images along with their search queries, source titles, source URLs, and context snippets.

Evaluate and score each image on a scale from 0 to 10 based on its relevance, utility, and quality for the report.
Calculate the relevance score using:
1. Report Topic: Does the image's source title and snippet context align with the report topic?
2. Image Title & Metadata: Does the page title and query indicate it's a high-quality relevant illustration (portraits of people, diagrams, timeline infographics)?
3. Image Source Context: Evaluate the context snippet. Discard images from irrelevant, desktop setup screenshots, or low-quality contexts.

Rules:
1. Boost (+3 to +5): Diagrams, infographics, portraits/photos of key people, historical photographs, architecture images.
2. Penalize (-5 to -10): Desktop environment screenshots, UI screenshots, window menus, simple plain logos only (unless it is a famous mascot like Tux), watermarked/stock images.
3. Deduplicate: If multiple URLs represent the same visual content or key subject, score the duplicates 0 (only keep the best one).

Candidate Images:
{json.dumps(candidates, indent=2)}

Return the results as a JSON array of objects, containing ONLY the "url", "score", and a brief "reason". Order the array by score descending.
Return ONLY valid JSON:
[
  {{"url": "...", "score": 8, "reason": "..."}},
  ...
]
"""
        scoring_resp = generate(scoring_prompt).strip()
        start = scoring_resp.find("[")
        end = scoring_resp.rfind("]")
        if start != -1 and end != -1 and end > start:
            parsed = json.loads(scoring_resp[start:end+1])
            parsed = sorted(parsed, key=lambda x: x.get("score", 0), reverse=True)
            final_images = [img["url"] for img in parsed if img.get("score", 0) > 4][:3]
            if final_images:
                print(f"Successfully scored and selected {len(final_images)} images.")
                return final_images

    except Exception as e:
        print(f"Failed to fetch and score report images: {e}")
        
    # Fallback deduplication and basic screen/watermark filtering
    fallback_images = []
    try:
        for c in candidates:
            url_lower = c["url"].lower()
            if any(x in url_lower for x in ["screenshot", "desktop", "ui", "menu", "watermark"]):
                continue
            if c["url"] not in fallback_images:
                fallback_images.append(c["url"])
    except Exception:
        pass
    return fallback_images[:3]


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
        images=images
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

    if not is_failed:
        save_research(
            query=state["query"],
            route=state["route"],
            report=formatted_report,
            sources=state.get("sources", []),
            insights=insights
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
        sources=[]
    )

    insights = {
        "word_count": len(state["rag_answer"].split()),
        "reference_count": 0,
        "references_used": 0,
        "unique_sources": 0,
        "average_source_freshness": "N/A",
        "citation_density": 0.0,
        "evidence_coverage": 0.0,
        "evidence_panel": []
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
    from agents.arxiv_agent import search_arxiv
    query = state["query"]
    
    try:
        results = search_arxiv(query)
    except Exception as e:
        print(f"arXiv search failed: {e}. Falling back to WEB route.")
        results = []

    if len(results) < 5:
        from agents.arxiv_agent import expand_academic_queries
        print("Expanding queries to meet minimum source threshold for arXiv...")
        try:
            expanded = expand_academic_queries(query)
            seen_urls = {r.get("url") for r in results if r.get("url")}
            for q in expanded:
                if len(results) >= 6:
                    break
                if q.lower() == query.lower():
                    continue
                try:
                    more_results = search_arxiv(q)
                    for mr in more_results:
                        url = mr.get("url")
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
        r["priority"] = get_source_priority(r.get("url", ""), "arxiv")
    results.sort(key=lambda x: x["priority"])

    sources = []
    processed_sources = []
    for idx, paper in enumerate(results[:8], start=1):
        year = paper["published"][:4] if paper.get("published") else "Unknown"
        authors_str = ", ".join(paper["authors"]) if paper.get("authors") else "Unknown"
        item = {
            "title": paper["title"],
            "url": paper["url"],
            "authors": authors_str,
            "year": year,
            "content": paper["summary"],
            "raw_content": paper["summary"],
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