import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)


def review_report(
    query,
    report
):

    prompt = f"""
You are a senior research reviewer.

Research Topic:
{query}

Below is a draft report.

REPORT:
{report}

Your job is to improve it.

Check for:

1. Missing information
2. Weak arguments
3. Unsupported claims
4. Poor structure
5. Missing counterarguments

Return an improved version of the report.

Do not explain your review process.

Return only the improved report.
"""

    response = client.chat.completions.create(
        model="google/gemini-3.1-flash-lite",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        max_tokens=1500
    )

    return (
        response
        .choices[0]
        .message
        .content
    )