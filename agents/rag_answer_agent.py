from llm.groq_client import generate


def generate_rag_answer(
    query,
    retrieved_chunks
):

    context = "\n\n".join(
        retrieved_chunks
    )

    prompt = f"""
Answer the user's question using ONLY the provided context.

If the answer is not present in the context,
say:

"I could not find this information in the local knowledge base."

QUESTION:
{query}

CONTEXT:
{context}
"""

    try:

        return generate(prompt)

    except Exception as e:

        return f"""
I could not generate an answer.

Error:
{str(e)}
"""