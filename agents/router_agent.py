import re
from llm.gemini_client import generate as gemini_generate

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
    query = query.lower()

    # Return ARXIV only when academic intent is strongly detected via keywords
    if detect_academic_query(query):
        return "ARXIV"

    classification_prompt = f"""
Classify the following query into exactly one of three categories:
- ACADEMIC: ONLY classify the query as ACADEMIC if it is a technical, scientific research query suited for the arXiv database (specifically: computer science, machine learning, deep learning, artificial intelligence, physics, mathematics, statistics, electrical engineering, quantitative biology, quantitative finance). Do NOT classify psychology, social sciences, medicine, psychiatry, human behavior, anger management, history, culture, cinema, art, geography, business, or literature topics as ACADEMIC, even if they contain formal or scientific-sounding language. Route all of those to GENERAL instead.
- GENERAL: If the query is about pop culture, movies, cinema history, general history, psychology, human behavior, social sciences, anime, news, fictional characters, general trivia, geography, or sports (e.g. Optimus Prime, Megatron, Autobots vs Decepticons, Naruto, Growth of Indian cinema in the 20's, Anger management in Gen-Z).
- AMBIGUOUS: If the query is vague, short, or unclear.

Query: "{query}"

Output exactly one word: ACADEMIC, GENERAL, or AMBIGUOUS.
"""
    try:
        response = gemini_generate(classification_prompt).strip().upper()
        if "ACADEMIC" in response:
            return "ARXIV"
    except Exception as e:
        print(f"Gemini routing classification failed: {e}")

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
        if keyword in query:
            return "HYBRID"

    # WEB third

    for keyword in web_keywords:
        if keyword in query:
            return "WEB"

    # RAG fourth

    for keyword in rag_keywords:
        if keyword in query:
            return "RAG"

    return "WEB"