import ollama


def review_report(
    query,
    report
):

    prompt = f"""
You are a senior research reviewer.

Research Topic:
{query}

Below is a draft report.

REPORT:
{report}

Your job is to improve it.

Check for:

1. Missing information
2. Weak arguments
3. Unsupported claims
4. Poor structure
5. Missing counterarguments

Return an improved version of the report.

Do not explain your review process.

Return only the improved report.
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

        return response["message"]["content"]

    except Exception as e:

        print(
            f"Critic Agent Error: {e}"
        )

        return report