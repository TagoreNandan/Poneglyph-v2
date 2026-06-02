def classify_query(query):

    query = query.lower()

    rag_keywords = [
        "langgraph",
        "chromadb",
        "rag",
        "retrieval augmented generation"
    ]

    hybrid_keywords = [
        "compare",
        "comparison",
        "vs",
        "versus",
        "difference"
    ]

    web_keywords = [
        "latest",
        "today",
        "recent",
        "current",
        "news",
        "2025",
        "2026",
        "trend",
        "trends"
    ]

    # HYBRID

    for keyword in hybrid_keywords:
        if keyword in query:
            return "HYBRID"

    # RAG

    for keyword in rag_keywords:
        if keyword in query:
            return "RAG"

    # Everything else → WEB

    return "WEB"