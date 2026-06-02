from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"

model = SentenceTransformer(
    MODEL_NAME
)

def get_embedding(text: str):

    embedding = model.encode(
        text,
        convert_to_numpy=True
    )

    return embedding.tolist()