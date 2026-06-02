import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)


def generate_research_summary(query, search_results):

    formatted_results = ""

    for idx, result in enumerate(search_results[:3], start=1):

        content = (
    result.get("raw_content")
    or result.get("content")
    or result.get("summary")
    or ""
)

        formatted_results += f"""
=========================
SOURCE {idx}
=========================

TITLE:
{result['title']}

URL:
{result['url']}

CONTENT:
{str(content)[:3000]}

"""

    prompt = f"""
You are an expert research analyst.

Research Topic:
{query}

Below are multiple sources collected from the web.

{formatted_results}

Analyze all sources together and generate:

1. Executive Summary
2. Key Findings
3. Emerging Trends
4. Conflicting Opinions (if any)
5. Recommended Reading

Base your report on evidence from the sources.

Mention when multiple sources agree on a finding.
"""

    response = client.chat.completions.create(
        model="google/gemini-3.1-flash-lite",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        max_tokens=1000
    )

    return response.choices[0].message.content