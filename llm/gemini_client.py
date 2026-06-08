from dotenv import load_dotenv
from google import genai
import os

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

import time

def generate(prompt, model="gemini-2.5-flash"):
    response = client.models.generate_content(
        model=model,
        contents=prompt
    )
    return response.text