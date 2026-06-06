from llm.groq_client import generate


def generate_research_summary(
    query,
    search_results
):

    formatted_results = ""

    for idx, result in enumerate(
        search_results[:3],
        start=1
    ):

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
{str(content)[:4000]}
"""

    prompt = f"""
You are a senior research analyst.

Research Topic:
{query}

Sources:

{formatted_results}

You are a senior industry analyst.

Do not summarize sources individually.

Instead:

- Synthesize information across all sources
- Compare viewpoints
- Explain why findings matter
- Identify patterns
- Identify implications
- Draw conclusions from evidence
- Avoid repeating source text
- Provide expert analysis

Every section should contain reasoning,
not just facts.

Focus on insight generation,
not summarization.

Requirements:

- Target length: 600-800 words
- Use information from all available sources
- Mention when sources agree
- Mention disagreements when they exist
- Avoid repeating information
- Use concise analytical writing
- Support findings with evidence from sources
- Use bullet points where appropriate

Structure:

# Executive Summary

Brief overview of the topic and major conclusions.

# Key Findings

Summarize the most important findings from the sources.

# Emerging Trends

Identify patterns, innovations, and future developments.

# Conflicting Opinions

Mention disagreements or write "No significant conflicts found."

# Recommendations

Suggest next steps, practical implications, or areas for further research.

# Conclusion

Provide a concise closing summary.

Return valid markdown only.
"""

    try:

        return generate(prompt)

    except Exception as e:

        return f"""
# Error

Research generation failed.

Details:
{str(e)}
"""