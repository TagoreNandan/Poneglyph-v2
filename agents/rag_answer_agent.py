from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)


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

    response = client.chat.completions.create(
        model="openrouter/auto",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        max_tokens=500
    )

    return (
        response
        .choices[0]
        .message
        .content
    )