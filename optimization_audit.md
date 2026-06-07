# Poneglyph v2 Optimization Audit

Based on a deep analysis of API performance, LangGraph execution, source handling, and Gemini usage, here are the top 5 high-impact optimizations that should be addressed. 

---

### 1. Eliminate Source Truncation in `research_agent.py`
**Observation**: While the `reader_agent.py` processes up to 5 sources, the `research_agent.py` explicitly throws away data by looping over `search_results[:3]` (discarding 40% of the sources) and slicing the content with `content[:4000]`. 
**Expected Impact**: Fixing this will drastically improve report richness and factual depth, as Gemini 2.5 Flash easily supports massive context limits.
**Complexity**: Low
**Deploy Priority**: **Must fix before deployment.**

### 2. Implement Asynchronous Node Execution
**Observation**: The `reader_node` in `graph.py` summarizes sources sequentially (`for source in state["search_results"][:5]`). Because it waits for the LLM to respond before starting the next source, the pipeline takes 5x longer than necessary. Furthermore, the FastAPI endpoints in `api.py` are fully synchronous.
**Expected Impact**: Utilizing `asyncio.gather` for parallel LLM summarization and migrating the API endpoints to `async def` will speed up the entire research generation process by up to 400% and prevent HTTP connection timeouts.
**Complexity**: Medium
**Deploy Priority**: **Must fix before deployment** to prevent UI timeouts.

### 3. Implement Context-Aware LLM Fallback Routing
**Observation**: We recently added a Groq fallback in the `research_agent.py`. However, Gemini 2.5 Flash has a 1 Million token context window, while Groq's Llama models typically restrict to 8k tokens. If Gemini fails and falls back on a massive source payload, Groq will instantly crash with a context-length error.
**Expected Impact**: The fallback logic should be optimized to dynamically chunk or slice the `prompt` payload *only* if the request routes to Groq, ensuring true resilience.
**Complexity**: Low
**Deploy Priority**: **Must fix before deployment.**

### 4. Migrate to Real-Time Streaming (SSE)
**Observation**: The React frontend currently sits on a static "Agents are synthesizing data..." spinner for 15–40 seconds while LangGraph executes. The Agent Activity log is only populated retroactively.
**Expected Impact**: Upgrading `api.py` to stream LangGraph state updates via Server-Sent Events (SSE) will allow the Agent Activity Log to render dynamically in real-time, drastically improving the perceived performance and "SaaS feel" of the application.
**Complexity**: Medium/High
**Deploy Priority**: Optional for MVP, but highly recommended for V2.

### 5. Enhance Retrieval via Sub-Query Generation
**Observation**: `search_agent.py` directly executes the exact string the user typed (e.g. "Major natural disasters"). Broad queries return generic overview pages.
**Expected Impact**: Introducing a micro-node before `search_node` that uses Gemini to expand the broad query into 3 highly targeted sub-queries (e.g., "List of deadliest historical earthquakes", "Costliest natural disasters history") would massively improve the precision and quality of the Tavily retrieval.
**Complexity**: Medium
**Deploy Priority**: Optional. Can be added post-deployment.
