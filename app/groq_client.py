from openai import OpenAI
import os
client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

def summarize_bug(context_text: str) -> str:
    response = client.chat.completions.create(
        model=os.getenv("GROQ_MODEL"),
        messages=[
            {"role": "system", "content": "summarize this bug report clearly"},
            {"role": "user", "content": context_text}
        ]
    )
    return response.choices[0].message.content.strip()
