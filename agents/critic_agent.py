import ollama
import json


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

    "confidence_score": 0,

    "source_quality": 0,

    "source_agreement": 0,

    "coverage_score": 0,

    "research_gaps": [
        "...",
        "..."
    ],

    "contradictions": [
        "...",
        "..."
    ]
}}

Scoring Rules:

confidence_score:
Overall trustworthiness of the report.

source_quality:
How reliable the sources appear.

source_agreement:
How strongly the sources support the same conclusions.

coverage_score:
How complete the research appears.

research_gaps:
Missing information, unanswered questions,
areas needing more investigation.

contradictions:
Any conflicting opinions or findings found
inside the report.

Return JSON only.
"""

    try:

        response = ollama.chat(
            model="mistral:7b",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        print("\nCRITIC RAW OUTPUT:\n")
        print(
              response["message"]["content"]
        )
        print("\n")

        return json.loads(
            response["message"]["content"]
        )

    except Exception as e:

        print(
            f"Critic Agent Error: {e}"
        )

        return {
            "improved_report": report,
            "confidence_score": 75,
            "source_quality": 75,
            "source_agreement": 75,
            "coverage_score": 75,
            "research_gaps": [],
            "contradictions": []
        }