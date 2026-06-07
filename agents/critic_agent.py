import ollama
import json
from llm.gemini_client import generate


def review_report(
    query,
    report
):

    prompt = f"""
You are a senior research reviewer.

Research Topic:
{query}

REPORT:
{report}

Analyze the report and return ONLY valid JSON.

JSON format:

{{
    "improved_report": "...",

    "contradictions": [
        "...",
        "..."
    ]
}}

Scoring Rules:

contradictions:
Any conflicting opinions or findings found
inside the report.

Return JSON only.
"""

    try:

        # response = ollama.chat(
        #     model="mistral:7b",
        #     messages=[
        #         {
        #             "role": "user",
        #             "content": prompt
        #         }
        #     ]
        # )
        # output = response["message"]["content"]
        
        output = generate(prompt)

        print("\nCRITIC RAW OUTPUT:\n")
        print(output)
        print("\n")

        start_idx = output.find('{')
        end_idx = output.rfind('}')
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            output = output[start_idx:end_idx+1]

        return json.loads(output)

    except Exception as e:

        print(
            f"Critic Agent Error: {e}"
        )

        return {
            "improved_report": report,
            "contradictions": []
        }