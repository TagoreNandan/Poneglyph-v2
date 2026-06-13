import sys
from graph import graph

query = "Dragon Ball"

print(f"==================================================")
print(f"TESTING TOPIC: {query}")
print(f"==================================================")

try:
    result = graph.invoke({"query": query, "bypass_ambiguity": True})
    
    report = result.get("formatted_report", "")
    if not report or "temporarily unavailable" in report.lower() or "failed" in report.lower()[:100]:
        print("FAIL: Fallback report detected.")
    else:
        print("PASS: Full report generated.")
        
    print(f"Report length: {len(report)} characters")
    
except Exception as e:
    print(f"EXCEPTION ENCOUNTERED: {e}")
