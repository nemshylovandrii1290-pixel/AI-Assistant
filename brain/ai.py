from openai import OpenAI

from utils.config import OPENAI_API_KEY, OPENAI_MODEL

client = OpenAI(api_key=OPENAI_API_KEY)

def ask_ai(text):
  response = client.responses.create(
    model=OPENAI_MODEL,
    input=[{"role": "user", "content": text}]
  )

  return response.output[0].content[0].text


