from pathlib import Path

from rag.embeddings import get_embedding
from rag.vector_store import get_collection

collection = get_collection()

DATA_FOLDER = "data"


def ingest_documents():

    files = Path(
        DATA_FOLDER
    ).glob("*.txt")

    doc_count = 0

    for file in files:

        text = file.read_text(
            encoding="utf-8"
        )

        chunks = text.split("\n\n")

        for idx, chunk in enumerate(chunks):

            chunk = chunk.strip()

            if not chunk:
                continue

            embedding = get_embedding(
                chunk
            )

            collection.add(
                ids=[
                    f"{file.stem}_{idx}"
                ],
                documents=[
                    chunk
                ],
                embeddings=[
                    embedding
                ]
            )

            doc_count += 1

    print(
        f"{doc_count} chunks added."
    )


if __name__ == "__main__":

    ingest_documents()