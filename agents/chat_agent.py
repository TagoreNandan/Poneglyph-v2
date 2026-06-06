import ollama


def chat_with_report(
    report,
    question,
    chat_history
):

    history_text = ""

    for msg in chat_history:

        history_text += f"""
User:
{msg['question']}

Assistant:
{msg['answer']}
"""

    prompt = f"""
You are ResearchPilot AI.

Use the report and previous conversation
to answer the user's follow-up question.

REPORT:

{report}

CHAT HISTORY:

{history_text}

QUESTION:

{question}
"""

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