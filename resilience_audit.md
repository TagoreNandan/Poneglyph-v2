# Resilience Audit & Dependency Map

## 1. Primary Dependencies
**All agents** currently depend on **Gemini 2.5 Flash** as their primary inference engine.

## 2. Secondary Dependencies (Groq)
The following agents depend on **Groq** as an active secondary fallback:
- `reader_agent.py`
- `research_agent.py`

## 3. Ollama References
The following agents contain commented-out, inactive references to local **Ollama**:
- `critic_agent.py`
- `chat_agent.py`

## 4. Single Points of Failure
If Gemini returns 503 and Groq hits quota limits, the following happens:
- **`chat_agent.py`**: **Completely Fails.** Has no `try/except` block and no fallbacks. Will instantly crash the graph.
- **`rag_answer_agent.py`**: Fails gracefully. Returns a hardcoded error string ("I could not generate an answer").
- **`reader_agent.py`**: Fails gracefully. Returns a hardcoded error string.
- **`research_agent.py`**: Fails gracefully. Returns a markdown error report.
- **`critic_agent.py`**: Degrades gracefully. Fails parsing and returns the default `75` metrics dictionary.

## 5. Active Fallback Paths
* **Reader Agent:** Gemini → Groq → Exception String
* **Research Agent:** Gemini → Groq → Markdown Error Report
* **Critic Agent:** Gemini → Default 75 metrics
* **Chat Agent:** Gemini → **Hard Crash**
* **RAG Agent:** Gemini → Exception String

---

## Recommendation: The "Indestructible Local Fallback"
The smallest possible change to make the system highly resilient is to **activate local Ollama as the absolute final layer of defense.** 

Since you are already running `ollama serve` with `mistral:7b` in the background, it has zero network dependencies and zero rate limits. 

**The Fix:**
In `reader_agent.py`, `research_agent.py`, and `chat_agent.py`, we can wrap the final Groq fallback (or Gemini call) in one more `try/except` block that imports `ollama` and executes `ollama.chat(model="mistral:7b")`. If the cloud is down, your local hardware will silently take over and draft the report, ensuring the pipeline never fails to return data.
