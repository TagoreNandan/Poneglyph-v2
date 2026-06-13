import sys
import json
sys.path.append('/Users/somespecies/Desktop/main projects/researchpilot for anti-gra')
from dotenv import load_dotenv
load_dotenv('.env')

from llm.groq_client import generate as groq_generate

import llm.gemini_client
llm.gemini_client.generate = groq_generate

from graph import fetch_report_images

topics = ['Formula One', 'One Piece', 'Apple', 'Cristiano Ronaldo']
for topic in topics:
    print(f'\n--- Testing {topic} ---')
    try:
        images = fetch_report_images(topic)
        print(f'Final images for {topic}: {images}')
    except Exception as e:
        print(f'Error for {topic}: {e}')
