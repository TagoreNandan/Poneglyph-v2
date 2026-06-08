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

IMPORTANT PRIORITY INSTRUCTION:
The sources provided above are ordered by authority and priority (Priority 1 sources like Academic/Government appear first, Priority 5 sources like Community forums appear last). You MUST give higher priority sources significantly more weight and influence when synthesizing findings and drawing conclusions.

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

# [Adapt Heading Based on Topic]
(Choose ONE heading: "Recommendations" for business/policy, "Future Research Directions" for academic/scientific, or "Key Takeaways" for historical/fictional/entertainment)

Suggest next steps, practical implications, or areas for further research based on the topic.

# Conclusion

Provide a concise closing summary.

Return valid markdown only.
"""

    import time
    import sys

    providers = [
        ("Gemini", gemini_generate, "gemini-2.5-flash"),
        ("Groq", groq_generate, "llama-3.3-70b-versatile"),
        ("Gemini", gemini_generate, "gemini-1.5-pro"),
        ("Groq", groq_generate, "llama-3.1-8b-instant")
    ]
    
    backoff = [2, 5, 10]
    
    for i, (provider_name, func, model) in enumerate(providers):
        for attempt in range(4): # 1 initial + 3 retries
            start_time = time.time()
            try:
                print(f"DIAGNOSTIC: Provider selected: {provider_name}")
                if attempt > 0:
                    print(f"DIAGNOSTIC: Retry count: {attempt}")
                result = func(prompt, model=model)
                duration = time.time() - start_time
                print(f"Provider {provider_name} ({model}) succeeded on attempt {attempt+1}. Duration: {duration:.2f}s")
                return result
            except Exception as e:
                duration = time.time() - start_time
                error_msg = str(e).lower()
                is_transient = any(x in error_msg for x in ["429", "500", "503", "timeout", "unavailable", "rate limit", "temporarily", "server error"])
                
                print(f"FAILED: Provider={provider_name}, Model={model}, Reason={e}, Status=Error, RetryCount={attempt}, Duration={duration:.2f}s", file=sys.stderr)
                
                if is_transient and attempt < 3:
                    sleep_time = backoff[attempt]
                    print(f"Retrying {provider_name} ({model}) in {sleep_time}s...", file=sys.stderr)
                    time.sleep(sleep_time)
                else:
                    if i < len(providers) - 1:
                        next_provider = providers[i+1]
                        print(f"DIAGNOSTIC: Fallback provider selected: {next_provider[0]}")
                        print(f"Selected fallback provider: {next_provider[0]} ({next_provider[2]})", file=sys.stderr)
                    else:
                        print("CRITICAL: All research providers failed.", file=sys.stderr)
                        return """# Research Report

Research generation could not be completed at this time.

Please try again shortly."""
                    break # Break inner retry loop to move to next provider