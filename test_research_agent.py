from agents.research_agent import (
    generate_research_summary
)

dummy_data = [
    {
        "title": "LangGraph",
        "url": "https://langchain.com",
        "summary": "LangGraph is a framework for building stateful agent workflows."
    }
]

result = generate_research_summary(
    "What is LangGraph?",
    dummy_data
)

print(result)