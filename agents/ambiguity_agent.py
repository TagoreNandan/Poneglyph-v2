import json
from llm.gemini_client import generate

def detect_ambiguity(query: str):
    prompt = f"""
    Analyze the following search query: "{query}"
    
    If the query is highly ambiguous with multiple common distinct interpretations (e.g., "Apple", "Java", "The Big Three"), return "needs_clarification": true and provide 3-4 specific options in "options". Add "Other" as the last option.
    If the query is clear enough for research, return "needs_clarification": false.
    
    Return ONLY valid JSON:
    {{
        "needs_clarification": true/false,
        "options": ["option 1", "option 2", "Other"]
    }}
    """
    try:
        output = generate(prompt)
        start = output.find('{')
        end = output.rfind('}')
        if start != -1 and end != -1 and end > start:
            parsed = json.loads(output[start:end+1])
            
            if parsed.get("needs_clarification"):
                options = parsed.get("options", [])
                
                # Filter out "Other" if it exists so we can firmly place it at the end
                options = [opt for opt in options if opt.lower() != "other"]
                
                # Truncate to max 3 specific options
                options = options[:3]
                
                # Append "Other"
                options.append("Other")
                
                parsed["options"] = options
                
            return parsed
        return {"needs_clarification": False, "options": []}
    except Exception as e:
        print(f"Ambiguity Agent Error: {e}")
        return {"needs_clarification": False, "options": []}
