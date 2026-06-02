from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)


def summarize_source(source):

    content = source.get(
        "raw_content",
        source.get("content", "")
    )

    prompt = f"""
You are a research analyst.

Read the source below and create:

1. Short Summary
2. Key Findings (bullet points)

SOURCE:

Title: {source['title']}

Content:
{content[:3000]}
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

    summary = response.choices[0].message.content
    
    if summary is None:
        summary = "No summary available."
    
    return {
        "title": source["title"],
        "url": source["url"],
        "content": summary
    }