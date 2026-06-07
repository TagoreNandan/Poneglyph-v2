from llm.gemini_client import generate as gemini_generate
from llm.groq_client import generate as groq_generate


def generate_research_summary(
    query,
    search_results,
    route="WEB"
):

    formatted_results = ""

    for idx, result in enumerate(
        search_results,
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
{result.get('title', 'Unknown Title')}

URL:
{result.get('url', '')}

AUTHORS:
{result.get('authors', 'Unknown Authors')}

YEAR:
{result.get('year', 'Unknown Year')}

CONTENT:
{str(content)[:25000]}
"""

    if route == "ARXIV":
        prompt = f"""
You are a senior academic research reviewer.

Research Topic:
{query}

Sources:

{formatted_results}

For each source listed above, you MUST write a structured review following this exact format. Do not skip any sections.

# [Real Paper Title]
**Authors**: [Real Authors]
**Year**: [Real Year]
**URL**: [Real URL]

## Abstract Summary
[Write a concise summary of the abstract of the paper based strictly on the provided content]

## Key Contributions
[Write bullet points of the paper's key contributions and findings]

## Limitations
[Write a short analysis of the limitations or gaps of this paper based on the content]

---

Requirements:
- You must review every provided paper.
- Use the real metadata of the paper (Title, Authors, Year, URL). Do not fabricate paper titles, authors, years, or URLs.
- Cite the paper using its index (e.g. `[1]` for the first paper, `[2]` for the second) at the end of statements. Place citations like `[1]` before periods or punctuation.
- Return valid markdown only.
"""
    else:
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
- Support findings with evidence from sources using inline citation markers (e.g., `[1]`, `[2]`, `[1][3]` if synthesized).
- You MUST append citation markers to every factual statement or claim. Example: "ARPANET adopted TCP/IP in 1983.[1]"
- Do NOT fabricate citations. Do NOT invent citation numbers. Only use indices matching the provided sources (e.g. `[1]` to `[{len(search_results)}]`).
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
        return gemini_generate(prompt)
    except Exception as e:
        error_str = str(e).lower()
        if any(x in error_str for x in ["429", "500", "503", "timeout", "rate limit"]):
            try:
                return groq_generate(prompt)
            except Exception as fallback_e:
                e = f"Gemini Error: {str(e)}\nGroq Fallback Error: {str(fallback_e)}"
        
        import sys
        import traceback
        print(f"CRITICAL: Research Generation Failed. Exception details:\n{e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        
        return """# Research Report

Report generation temporarily unavailable.

All research providers are currently busy or unavailable.

Please try again in a few minutes.

No report was generated."""