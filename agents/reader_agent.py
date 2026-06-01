import requests
from bs4 import BeautifulSoup


def extract_article_text(url: str, max_chars: int = 5000):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=10
        )

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        paragraphs = soup.find_all("p")

        text = " ".join(
            p.get_text(strip=True)
            for p in paragraphs
        )

        return text[:max_chars]

    except Exception as e:
        return f"Error reading {url}: {str(e)}"