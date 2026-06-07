from llm.gemini_client import generate as gemini_generate
from llm.groq_client import generate as groq_generate


def summarize_source(source):
    content = (
        source.get("raw_content")
        or source.get("content")
        or ""
    )
    
    # Return directly truncated content to save Gemini calls/tokens
    truncated = content.strip()
    if len(truncated) > 5000:
        truncated = truncated[:5000] + "..."
        
    return {
        "title": source["title"],
        "url": source["url"],
        "content": truncated
    }