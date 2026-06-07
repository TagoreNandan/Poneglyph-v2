from llm.gemini_client import generate as gemini_generate

def classify_query(query):

    query = query.lower()

    # Use Gemini to classify the query type
    classification_prompt = f"""
Classify the following query into exactly one of three categories:
- ACADEMIC: If the query is a genuine academic or technical research query (e.g. machine learning, neural networks, computer vision, BERT paper, Transformer architecture).
- GENERAL: If the query is about pop culture, movies, anime, news, fictional characters, general topics (e.g. Optimus Prime, Megatron, Autobots vs Decepticons, Naruto, One Piece, anime).
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