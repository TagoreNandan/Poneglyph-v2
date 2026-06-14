#import ollama
import json
from llm.gemini_client import generate


def review_report(
    query: str,
    report: str,
    verified_claims: list = None
) -> dict:

    if verified_claims:
        # Format verified claims
        formatted_claims = ""
        for idx, vc in enumerate(verified_claims, start=1):
            claim = vc.get("claim", "")
            status = vc.get("status", "UNVERIFIED")
            evidence = ", ".join(vc.get("evidence", []))
            formatted_claims += f"- [{status}] Claim: {claim}\n  Evidence: {evidence}\n\n"

        prompt = f"""
You are a senior research reviewer.

Research Topic:
{query}

REPORT:
{report}

Verification Data (Status and Evidence for key claims in the report):
{formatted_claims}

Analyze the report, review the verification data, and return ONLY valid JSON.

Your review task:
1. Carefully review disputed and weak claims identified in the verification data.
2. Highlight any unsupported assertions in the report.
3. Recommend or perform edits in the report to address areas requiring stronger evidence or corrections based on the verification data.
4. Output the final, corrected/improved report in the "improved_report" key.

JSON format:
{{
    "improved_report": "..."
}}

Return JSON only.
"""
    else:
        prompt = f"""
You are a senior research reviewer.

Research Topic:
{query}

REPORT:
{report}

Analyze the report and return ONLY valid JSON.

JSON format:

{{
    "improved_report": "..."
}}

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
        
        try:
            output = generate(prompt)
        except Exception as gemini_err:
            import logging
            logging.getLogger(__name__).warning("Critic Agent: Gemini call failed. Activating Groq fallback.", exc_info=True)
            from llm.groq_client import generate as groq_generate
            output = groq_generate(prompt)

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
            "improved_report": report
        }