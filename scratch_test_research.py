import sys
import asyncio
sys.path.append('/Users/somespecies/Desktop/main projects/researchpilot for anti-gra')
from dotenv import load_dotenv
load_dotenv('.env')

from agents.research_agent import generate_research_summary

print("Running generate_research_summary...")
try:
    sources = []
    for i in range(5):
        sources.append({
            "title": f"Source {i+1}",
            "content": "A" * 25000,
            "url": f"http://example.com/{i+1}"
        })
    result = generate_research_summary(query="Formula One", search_results=sources, route="WEB")
    print("RESULT:")
    print(result)
except Exception as e:
    import traceback
    traceback.print_exc()
