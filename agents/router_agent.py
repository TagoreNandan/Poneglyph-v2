def classify_query(query):

    query = query.lower()

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

    # HYBRID first

    for keyword in hybrid_keywords:
        if keyword in query:
            return "HYBRID"

    # WEB second

    for keyword in web_keywords:
        if keyword in query:
            return "WEB"

    # RAG third

    for keyword in rag_keywords:
        if keyword in query:
            return "RAG"

    return "WEB"