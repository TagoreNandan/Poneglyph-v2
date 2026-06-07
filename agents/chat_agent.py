import re
from llm.gemini_client import generate
from agents.search_agent import search_web


def chat_with_report(
    report,
    question,
    chat_history
):

    history_text = ""

    for msg in chat_history:

        history_text += f"""
User:
{msg['question']}

Assistant:
{msg['answer']}
"""

    # 1. Parse original topic from report
    topic = ""
    lines = report.split("\n")
    try:
        idx = -1
        for i, line in enumerate(lines):
            if "## Topic" in line:
                idx = i
                break
        if idx != -1:
            for j in range(idx + 1, len(lines)):
                if lines[j].strip():
                    topic = lines[j].strip()
                    break
    except Exception:
        pass
    
    if not topic:
        topic = question # Fallback if parsing fails

    # 2. Generate search query using LLM
    search_query = question # Fallback
    try:
        query_prompt = f"""
Based on the original research topic and the user's follow-up question, generate a single concise search query optimized for search engines (like Google or Tavily) to find the relevant information to answer the follow-up question.
Do not include any search operators, quotation marks, or explanations. Output only the query string.

Original Topic: {topic}
Follow-up Question: {question}

Search Query:
"""
        generated_query = generate(query_prompt).strip().strip('"').strip("'")
        if generated_query:
            search_query = generated_query
    except Exception as e:
        print(f"Failed to generate search query for follow-up: {e}")

    # 3. Perform Tavily search for fresh content
    formatted_results = ""
    try:
        results = search_web(search_query)
        for idx, res in enumerate(results[:3], start=1):
            content = res.get("raw_content") or res.get("content") or ""
            formatted_results += f"Source {idx}: {res.get('title')}\nURL: {res.get('url')}\nContent: {content[:3000]}\n\n"
    except Exception as e:
        print(f"Tavily search for follow-up failed: {e}")

    # 4. Generate final answer with search context
    prompt = f"""
You are ResearchPilot AI.

Answer the user's follow-up question using the provided search results from the web, the original report context, and the conversation history.
Your answer must be directly supported by the search results. Use inline citation markers (e.g. [1], [2]) if referring to specific search result sources.

ORIGINAL REPORT CONTEXT:
{report}

CHAT HISTORY:
{history_text}

NEW SEARCH RESULTS:
{formatted_results}

QUESTION:
{question}
"""
    try:
        return generate(prompt)
    except Exception as e:
        # Fallback to pure-report context in case of LLM error
        fallback_prompt = f"""
You are ResearchPilot AI.

Use the report and previous conversation to answer the user's follow-up question.

REPORT:
{report}

CHAT HISTORY:
{history_text}

QUESTION:
{question}
"""
        try:
            return generate(fallback_prompt)
        except Exception:
            return "I'm sorry, the chat service is currently experiencing high load. Please try again in a moment."