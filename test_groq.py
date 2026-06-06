# test_groq.py

from llm.groq_client import generate

print(
    generate(
        "What is LangGraph? Explain in 2 sentences."
    )
)