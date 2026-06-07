from dotenv import load_dotenv
from google import genai
import os

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

import time

def generate(prompt):
    max_retries = 3
    backoff = [1, 2, 4]
    
    for attempt in range(max_retries + 1):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            if attempt > 0:
                print(f"Gemini call succeeded on attempt {attempt + 1}")
            return response.text
        except Exception as e:
            err_msg = str(e).lower()
            is_transient = any(x in err_msg for x in ["429", "500", "503", "timeout", "unavailable", "rate limit", "temporarily"])
            if is_transient and attempt < max_retries:
                sleep_time = backoff[attempt]
                print(f"Gemini call failed (attempt {attempt + 1}/{max_retries + 1}) due to transient error: {e}. Retrying in {sleep_time}s...")
                time.sleep(sleep_time)
            else:
                raise e