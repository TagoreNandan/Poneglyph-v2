# test_rag.py

from rag.embeddings import get_embedding
from rag.vector_store import get_collection

print(
    len(
        get_embedding(
            "Hello World"
        )
    )
)

print(
    get_collection().name
)