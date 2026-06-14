import re
from llm.gemini_client import generate as gemini_generate

def calculate_scores(query: str):
    normalized = query.lower()
    
    academic_score = 0
    company_score = 0
    
    # 1. Academic strong phrases / keywords
    strong_academic_phrases = [
        "latest research on",
        "survey papers on",
        "survey paper on",
        "state of the art",
        "sota",
        "academic benchmark",
        "academic benchmarks",
        "research paper",
        "research papers",
        "arxiv paper",
        "arxiv papers",
        "literature review"
    ]
    for phrase in strong_academic_phrases:
        if phrase in normalized:
            academic_score += 3
            
    academic_keywords = [
        "paper",
        "research",
        "study",
        "survey",
        "authors",
        "citation",
        "benchmark",
        "published",
        "arxiv",
        "scientific",
        "academic",
        "cosmology",
        "physics",
        "mathematical"
    ]
    for kw in academic_keywords:
        pattern = rf"\b{re.escape(kw)}\b"
        if re.search(pattern, normalized):
            academic_score += 1

    # Distinguish "anthropic principle" vs company "Anthropic"
    if "anthropic principle" in normalized or "anthropic cosmological" in normalized:
        academic_score += 3
    elif "anthropic" in normalized:
        # Check if it looks like the AI company (e.g. OpenAI vs Anthropic, Anthropic Claude, Anthropic company, etc.)
        company_score += 2

    # 2. Company / Commercial strong indicators
    strong_company_phrases = [
        "company overview",
        "earnings report",
        "financial results",
        "fiscal year",
        "market capitalization",
        "share price",
        "stock price",
        "funding round",
        "venture capital"
    ]
    for phrase in strong_company_phrases:
        if phrase in normalized:
            company_score += 3

    company_keywords = [
        "earnings",
        "valuation",
        "revenue",
        "stock",
        "stocks",
        "finance",
        "financial",
        "corporation",
        "corporate",
        "startup",
        "competitor",
        "competition",
        "merger",
        "acquisition",
        "ceo",
        "ipo",
        "company",
        "companies",
        "quarterly",
        "q1", "q2", "q3", "q4",
        "fiscal",
        "profit",
        "losses",
        "investor",
        "investors"
    ]
    for kw in company_keywords:
        pattern = rf"\b{re.escape(kw)}\b"
        if re.search(pattern, normalized):
            company_score += 1

    # Tech company names
    tech_companies = [
        "openai",
        "google",
        "microsoft",
        "nvidia",
        "tesla",
        "apple",
        "meta",
        "amazon",
        "claude",
        "gemini",
        "chatgpt"
    ]
    for company in tech_companies:
        pattern = rf"\b{re.escape(company)}\b"
        if re.search(pattern, normalized):
            company_score += 2

    return academic_score, company_score

def detect_academic_query(query: str) -> bool:
    """
    Check if the query strongly indicates academic research intent based on keywords.
    """
    normalized = query.lower()
    academic_keywords = [
        "paper",
        "research",
        "study",
        "survey",
        "authors",
        "citation",
        "benchmark",
        "state of the art",
        "published",
        "arxiv",
        "scientific",
        "academic"
    ]
    for kw in academic_keywords:
        pattern = rf"\b{re.escape(kw)}\b"
        if re.search(pattern, normalized):
            return True
    return False

def classify_query(query: str) -> str:
    query_lower = query.lower()

    academic_score, company_score = calculate_scores(query_lower)
    allow_arxiv = (academic_score > 0) and (academic_score >= company_score)

    final_route = None

    # Shortcut directly to ARXIV if academic intent is strong and there are no company signals
    if allow_arxiv and detect_academic_query(query_lower) and company_score == 0:
        final_route = "ARXIV"

    if final_route is None and allow_arxiv:
        classification_prompt = f"""
Classify the following query into exactly one of three categories:
- ACADEMIC: ONLY classify the query as ACADEMIC if it is a technical, scientific research query suited for the arXiv database (specifically: computer science, machine learning, deep learning, artificial intelligence, physics, mathematics, statistics, electrical engineering, quantitative biology, quantitative finance). Do NOT classify psychology, social sciences, medicine, psychiatry, human behavior, anger management, history, culture, cinema, art, geography, business, or literature topics as ACADEMIC, even if they contain formal or scientific-sounding language. Route all of those to GENERAL instead.
- GENERAL: If the query is about pop culture, movies, cinema history, general history, psychology, human behavior, social sciences, anime, news, fictional characters, general trivia, geography, or sports (e.g. Optimus Prime, Megatron, Autobots vs Decepticons, Naruto, Growth of Indian cinema in the 20's, Anger management in Gen-Z).
- AMBIGUOUS: If the query is vague, short, or unclear.

Query: "{query}"

Output exactly one word: ACADEMIC, GENERAL, or AMBIGUOUS.
"""
        try:
            try:
                response = gemini_generate(classification_prompt).strip().upper()
            except Exception as gemini_err:
                import logging
                logging.getLogger(__name__).warning("Router Agent: Gemini call failed. Activating Groq fallback.", exc_info=True)
                from llm.groq_client import generate as groq_generate
                response = groq_generate(classification_prompt).strip().upper()
                
            if "ACADEMIC" in response:
                final_route = "ARXIV"
        except Exception as e:
            print(f"Routing classification failed: {e}")

    if final_route is None:
        web_keywords = [
            "latest",
            "today",
            "recent",
            "current",
            "news",
            "2025",
            "2026",
            "trend",
            "trends",
            "developments"
        ]

        hybrid_keywords = [
            "compare",
            "comparison",
            "vs",
            "versus",
            "difference"
        ]

        rag_keywords = [
            "langgraph",
            "chromadb",
            "rag",
            "retrieval augmented generation"
        ]

        # HYBRID second
        for keyword in hybrid_keywords:
            if keyword in query_lower:
                final_route = "HYBRID"
                break

        # WEB third
        if final_route is None:
            for keyword in web_keywords:
                if keyword in query_lower:
                    final_route = "WEB"
                    break

        # RAG fourth
        if final_route is None:
            for keyword in rag_keywords:
                if keyword in query_lower:
                    final_route = "RAG"
                    break

        if final_route is None:
            final_route = "WEB"

    print(f"academic_score={academic_score}")
    print(f"company_score={company_score}")
    print(f"final_route={final_route}")
    return final_route