import ollama


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

        response = ollama.chat(
            model="mistral:7b",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response["message"]["content"]

    except Exception as e:

        return f"""
I could not generate an answer.

Error:
{str(e)}
"""