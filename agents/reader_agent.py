import ollama


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
{content[:1000]}
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

        summary = response["message"]["content"]

        if not summary:
            summary = "No summary available."

    except Exception as e:

        summary = f"Failed to summarize source: {str(e)}"

    return {
        "title": source["title"],
        "url": source["url"],
        "content": summary
    }