import os
import openai

openai.api_key=os.getenv("GROQ_API_KEY")
openai.api_base="https://api.groq.com/openai/v1"

def summarize_bug(context_text:str)->str:
    response=openai.ChatCompletion.create(
        model=os.getenv("GROQ_MODEL"),
        messages=[
            {"role":"system","content":"summarize this bug report clearly"},{"role":"user","content":context_text}
        ]
    )
    return response.choices[0].message.content.strip()