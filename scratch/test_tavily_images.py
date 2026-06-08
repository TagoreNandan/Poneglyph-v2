import os
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()
client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

res = client.search(query="Linus Torvalds portrait", include_images=True)
print("=== IMAGES ===")
print(res.get("images"))
print("\n=== RESULTS KEYWORDS ===")
print(res.keys())
if res.get("results"):
    print("\n=== FIRST RESULT ===")
    print(res["results"][0])
