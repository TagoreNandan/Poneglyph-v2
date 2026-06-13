import sys
import asyncio
sys.path.append('/Users/somespecies/Desktop/main projects/researchpilot for anti-gra')
from dotenv import load_dotenv
load_dotenv('.env')

from agents.research_agent import generate_research_report

state = {
    "topic": "Formula One",
    "sources": [
        {"title": "Source 1", "content": "Dummy content 1"},
        {"title": "Source 2", "content": "Dummy content 2"}
    ]
}

print("Running generate_research_report...")
result = generate_research_report(state)
print("RESULT:")
print(result)
