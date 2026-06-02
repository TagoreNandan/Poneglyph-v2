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

    return results["documents"][0]