import sys
import os

workspace_dir = "/Users/somespecies/Desktop/main projects/researchpilot for anti-gra"
sys.path.append(workspace_dir)
os.chdir(workspace_dir)

from graph import graph

print("=== TESTING CINEMA QUERY ===")
res = graph.invoke({"query": "Growth of Indian cinema in the 20's", "bypass_ambiguity": True})
print("\n=== GRAPH COMPLETED ===")
print("Route Selected:", res.get("route"))
print("Word Count:", len(res.get("formatted_report", "").split()))

print("\n=== SOURCES CITED ===")
sources = res.get("sources", [])
for idx, s in enumerate(sources, start=1):
    print(f"[{idx}] {s.get('title')} | URL: {s.get('url')}")
    print(f"    Content snippet: {s.get('content')[:120]}...")

print("\n=== SELECTED IMAGES ===")
import re
images = re.findall(r'!\[.*?\]\((.*?)\)', res.get("formatted_report", ""))
for idx, img in enumerate(images, start=1):
    print(f"Image [{idx}]: {img}")
