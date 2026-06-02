from rag.retriever import retrieve
from agents.rag_answer_agent import (
    generate_rag_answer
)

query = "What is LangGraph?"

chunks = retrieve(
    query
)

answer = generate_rag_answer(
    query,
    chunks
)

print("\nANSWER:\n")
print(answer)