from rag.embeddings import get_embedding
from rag.vector_store import get_collection

collection = get_collection()


def retrieve(query, k=3):

    query_embedding = get_embedding(
        query
    )

    results = collection.query(
        query_embeddings=[
            query_embedding
        ],
        n_results=k
    )

    documents = results["documents"][0]
    distances = results["distances"][0]
    
    filtered = []
    for doc, dist in zip(documents, distances):
        # relevance score: 1.0 - (dist / 2.0)
        relevance = 1.0 - (dist / 2.0)
        if relevance >= 0.45:
            filtered.append(doc)
            
    return filtered