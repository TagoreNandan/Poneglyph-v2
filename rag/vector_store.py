import chromadb

client = chromadb.PersistentClient(
    path="./data/chroma_db"
)

collection = client.get_or_create_collection(
    name="poneglyph"
)

def get_collection():
    return collection