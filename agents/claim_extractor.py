import json
import logging
from typing import List, Dict, Any
from llm.gemini_client import generate as gemini_generate

logger = logging.getLogger(__name__)

def extract_claims(report_draft: str) -> List[Dict[str, Any]]:
    """
    Extracts factual claims from a research report draft using the Gemini model.
    
    Args:
        report_draft: The text of the research report draft.
        
    Returns:
        A list of dictionaries with structure:
        [
            {
                "claim": "...",
                "importance": 1-10
            }
        ]
    """
    logger.info("Starting claim extraction from report draft.")
    
    if not report_draft or not report_draft.strip():
        logger.warning("Empty report draft provided for claim extraction.")
        return []

    prompt = f"""
Analyze the following research report draft and extract all specific factual assertions/claims made within it.

Rules:
1. Extract ONLY factual assertions (e.g. statistics, dates, figures, specific historical events, technical features, or scientific findings).
2. Ignore opinions, recommendations, formatting templates, meta-commentary, or speculative conclusions.
3. For each claim, assign an importance score from 1 to 10 (10 being highly critical to the core theme, 1 being minor/supporting details).
4. Rank the extracted claims by importance in descending order.
5. Return ONLY a valid JSON list of objects.

Report Draft:
\"\"\"
{report_draft}
\"\"\"

Output format must be strictly a JSON array of objects like this:
[
  {{
    "claim": "The exact factual assertion here",
    "importance": 9
  }},
  ...
]

Do not include any explanation, markdown formatting blocks (like ```json), or extra text outside the JSON array. Output ONLY the raw JSON string.
"""

    try:
        try:
            response = gemini_generate(prompt).strip()
        except Exception as gemini_err:
            logger.warning("Claim Extractor: Gemini call failed. Activating Groq fallback.", exc_info=True)
            from llm.groq_client import generate as groq_generate
            response = groq_generate(prompt).strip()
        
        # Clean JSON output in case LLM wraps it in markdown code fences
        start_idx = response.find('[')
        end_idx = response.rfind(']')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_str = response[start_idx:end_idx+1]
        else:
            json_str = response

        claims = json.loads(json_str)
        
        # Validate schema and structure of output
        validated_claims = []
        if isinstance(claims, list):
            for item in claims:
                if isinstance(item, dict) and "claim" in item and "importance" in item:
                    try:
                        importance = int(item["importance"])
                        importance = max(1, min(10, importance)) # Clamp between 1 and 10
                    except (ValueError, TypeError):
                        importance = 5 # Fallback
                        
                    validated_claims.append({
                        "claim": str(item["claim"]).strip(),
                        "importance": importance
                    })
            
            # Sort descending by importance
            validated_claims.sort(key=lambda x: x["importance"], reverse=True)
            logger.info("Successfully extracted %d claims.", len(validated_claims))
            return validated_claims
        else:
            logger.error("Parsed JSON is not a list: %s", type(claims))
            return []
            
    except Exception as e:
        logger.error("Failed to extract claims: %s", e, exc_info=True)
        return []
