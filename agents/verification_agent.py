import os
import json
import time
import logging
from typing import List, Dict, Any
from tavily import TavilyClient
from llm.gemini_client import generate as gemini_generate

logger = logging.getLogger(__name__)

TRUST_SCORES = {
    # Official company domains
    "openai.com": 95,
    "anthropic.com": 95,
    "google.com": 95,
    "microsoft.com": 95,
    "nvidia.com": 95,
    "tesla.com": 95,

    # Academic
    "arxiv.org": 90,
    "nature.com": 90,
    "science.org": 90,

    # Major news
    "reuters.com": 85,
    "bloomberg.com": 85,
    "ft.com": 85,
    "wsj.com": 85,
    "cnbc.com": 80,
    "cnn.com": 80,

    # Technology publications
    "techcrunch.com": 75,
    "theverge.com": 75,
    "wired.com": 75,

    # Generic blogs
    "medium.com": 55,
    "substack.com": 55,

    # Community content
    "reddit.com": 45,
    "youtube.com": 40,
    "instagram.com": 30,
    "tiktok.com": 25
}

def get_trust_score(url: str) -> int:
    if not url:
        return 60
    url_lower = url.lower()
    # basic domain extraction
    domain = url_lower.split("://")[-1].split("/")[0].split("?")[0]
    if domain.startswith("www."):
        domain = domain[4:]
    
    # Check exact or suffix match
    if domain in TRUST_SCORES:
        return TRUST_SCORES[domain]
    
    for d, score in TRUST_SCORES.items():
        if domain == d or domain.endswith("." + d):
            return score
            
    # Suffix check for government and educational institutions
    if domain.endswith(".gov") or domain.endswith(".gov.uk") or ".gov." in domain:
        return 95
    if domain.endswith(".edu") or domain.endswith(".edu.cn") or ".edu." in domain:
        return 90
            
    return 60

def calculate_reliability_score(url: str, source_type: str = "web") -> tuple:
    if not url:
        return 70, "Corporate Blog"
    
    url_lower = url.lower()
    domain = url_lower.split("://")[-1].split("/")[0].split("?")[0]
    if domain.startswith("www."):
        domain = domain[4:]
        
    DOMAIN_RELIABILITY = {
        "openai.com": 95,
        "anthropic.com": 95,
        "deepmind.google": 95,
        "nature.com": 98,
        "arxiv.org": 90,
        "reuters.com": 95,
        "bloomberg.com": 95,
        "wsj.com": 90,
        "ft.com": 90,
        "coursera.org": 80,
        "github.com": 80,
        "reddit.com": 45,
        "youtube.com": 50
    }
    
    reliability = None
    if domain in DOMAIN_RELIABILITY:
        reliability = DOMAIN_RELIABILITY[domain]
    else:
        for d, r in DOMAIN_RELIABILITY.items():
            if domain == d or domain.endswith("." + d):
                reliability = r
                break
                
    if reliability is None:
        if ".gov" in domain:
            reliability = 95
        elif ".edu" in domain or source_type == "arxiv":
            reliability = 90
        else:
            reliability = 70
            
    official_domains = ["openai.com", "anthropic.com", "google.com", "microsoft.com", "nvidia.com", "tesla.com", "deepmind.google", "sec.gov"]
    academic_domains = ["arxiv.org", "nature.com", "science.org", "coursera.org"]
    news_domains = ["reuters.com", "bloomberg.com", "ft.com", "wsj.com", "cnbc.com", "cnn.com"]
    tech_domains = ["techcrunch.com", "theverge.com", "wired.com", "github.com"]
    community_domains = ["medium.com", "substack.com", "reddit.com", "youtube.com"]
    social_domains = ["instagram.com", "tiktok.com", "facebook.com", "twitter.com", "x.com", "pinterest.com"]

    dom_type = "Community"
    if any(d in domain for d in official_domains) or ".gov" in domain:
        dom_type = "Official"
    elif any(d in domain for d in academic_domains) or ".edu" in domain or source_type == "arxiv":
        dom_type = "Academic"
    elif any(d in domain for d in news_domains):
        dom_type = "Major News"
    elif any(d in domain for d in tech_domains):
        dom_type = "Technology Publication"
    elif any(d in domain for d in community_domains) or any(x in domain for x in ["forum", "forums", "community", "stackexchange", "stackoverflow", "fandom", "quora"]):
        dom_type = "Community"
    elif any(d in domain for d in social_domains):
        dom_type = "Social Media"
        
    return reliability, dom_type

def verify_serper_search(query: str) -> list:
    import requests
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
                "source": "serper"
            })
        return results
    except Exception as e:
        print(f"Serper verification search failed: {e}")
        return []

def verify_single_claim(claim: str, retries: int = 3) -> Dict[str, Any]:
    """
    Verifies a single factual claim by searching Tavily and comparing with Gemini.
    
    Args:
        claim: The text of the claim to verify.
        retries: Number of retry attempts on transient failures.
        
    Returns:
        A dictionary matching the schema:
        {
            "claim": "...",
            "status": "SUPPORTED" | "WEAK" | "DISPUTED" | "UNVERIFIED",
            "evidence": [...]
        }
    """
    logger.info("Verifying claim: '%s'", claim)
    
    search_results = []
    backoff = [2, 5, 10]
    use_serper = False
    
    print("Using Tavily verification search")
    # 1. Run targeted Tavily search with retry handling
    for attempt in range(retries):
        try:
            res = tavily_client.search(
                query=claim,
                max_results=3,
                search_depth="advanced"
            )
            search_results = res.get("results", [])
            if not search_results:
                use_serper = True
            break
        except Exception as e:
            logger.warning("Tavily search attempt %d failed for claim '%s': %s", attempt + 1, claim, e)
            if attempt < retries - 1:
                time.sleep(backoff[attempt])
            else:
                logger.error("Tavily search permanently failed for claim '%s'", claim)
                use_serper = True
                
    if use_serper:
        print("Tavily verification search failed, switching to Serper")
        search_results = verify_serper_search(claim)
        
    print(f"Verification evidence count: {len(search_results)}")
    
    # Calculate trust score and sort descending
    for r in search_results:
        url = r.get("url") or r.get("link") or ""
        r["trust_score"] = get_trust_score(url)
    search_results = sorted(search_results, key=lambda x: x.get("trust_score", 60), reverse=True)
    
    if not search_results:
        logger.info("No search results found for claim '%s'", claim)
        return {
            "claim": claim,
            "status": "UNVERIFIED",
            "evidence": [],
            "sources": []
        }
        
    # Format retrieved evidence context
    formatted_evidence = ""
    for idx, r in enumerate(search_results):
        title = r.get("title", "No Title")
        snippet = r.get("content", "")
        formatted_evidence += f"[{idx}] Title: {title}\nContent: {snippet}\n\n"
        
    # 2. Compare evidence against claim using Gemini with retry handling
    prompt = f"""
Verify the following claim using the provided search results as evidence.

Claim: "{claim}"

Search Results:
{formatted_evidence}

Based ONLY on the provided search results, determine if the claim is:
- SUPPORTED: Direct and strong evidence confirms the claim.
- WEAK: Some evidence supports the claim, but it is partial, lacks detail, or has minor inconsistencies.
- DISPUTED: Search results directly contradict or disprove the claim.
- UNVERIFIED: The provided search results do not contain enough relevant information to determine if the claim is true or false.

Return ONLY a valid JSON object matching this schema:
{{
  "status": "SUPPORTED" | "WEAK" | "DISPUTED" | "UNVERIFIED",
  "evidence": ["Exact sentence or snippet from the search results that supports/disputes/qualifies the claim"]
}}

Do not include any explanation, markdown formatting blocks (like ```json), or extra text outside the JSON block. Output ONLY the raw JSON string.
"""
    
    for attempt in range(retries):
        try:
            try:
                response = gemini_generate(prompt).strip()
            except Exception as gemini_err:
                logger.warning("Verification Agent: Gemini call failed. Activating Groq fallback.", exc_info=True)
                from llm.groq_client import generate as groq_generate
                response = groq_generate(prompt).strip()
            
            # Clean JSON wrapping code blocks
            start_idx = response.find('{')
            end_idx = response.rfind('}')
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                json_str = response[start_idx:end_idx+1]
            else:
                json_str = response
                
            data = json.loads(json_str)
            status = data.get("status", "UNVERIFIED").upper()
            if status not in ["SUPPORTED", "WEAK", "DISPUTED", "UNVERIFIED"]:
                status = "UNVERIFIED"
                
            evidence_list = data.get("evidence", [])
            if not isinstance(evidence_list, list):
                evidence_list = [str(evidence_list)] if evidence_list else []
                
            logger.info("Claim '%s' verification completed with status: %s", claim, status)
            return {
                "claim": claim,
                "status": status,
                "evidence": [str(e).strip() for e in evidence_list],
                "sources": [{"title": r.get("title", ""), "url": r.get("url", r.get("link", ""))} for r in search_results]
            }
        except Exception as e:
            logger.warning("Gemini verification attempt %d failed for claim '%s': %s", attempt + 1, claim, e)
            if attempt < retries - 1:
                time.sleep(backoff[attempt])
                
    logger.error("Gemini verification permanently failed for claim '%s'", claim)
    return {
        "claim": claim,
        "status": "UNVERIFIED",
        "evidence": [],
        "sources": [{"title": r.get("title", ""), "url": r.get("url", r.get("link", ""))} for r in search_results]
    }

def verify_claims(claims: List[Dict[str, Any]], limit: int = 10) -> List[Dict[str, Any]]:
    """
    Verifies a list of claims (limiting to top N claims).
    
    Args:
        claims: A list of dicts each containing 'claim' and optionally 'importance'.
        limit: The maximum number of claims to verify.
        
    Returns:
        A list of verified claim dicts.
    """
    logger.info("Verifying list of %d claims (limit=%d)", len(claims), limit)
    
    # Sort claims descending by importance
    sorted_claims = sorted(claims, key=lambda x: x.get("importance", 5), reverse=True)
    claims_to_verify = sorted_claims[:limit]
    
    verified_results = []
    for c in claims_to_verify:
        claim_text = c.get("claim")
        if claim_text:
            res = verify_single_claim(claim_text)
            verified_results.append(res)
            
    return verified_results
