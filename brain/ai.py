from openai import OpenAI

from utils.config import OPENAI_API_KEY, OPENAI_MODEL

client = OpenAI(api_key=OPENAI_API_KEY)

# 🔥 пам’ять
conversation = []

def ask_ai(text):
  global conversation

  conversation.append({
    "role": "user",
    "content": text
  })

  response = client.responses.create(
    model=OPENAI_MODEL,
    input=conversation
  )

  reply = response.output[0].content[0].text

  conversation.append({
    "role": "assistant",
    "content": reply
  })

  if len(conversation) > 20: # обмежуємо пам’ять до 20 повідомлень
    conversation = conversation[-20:]

  return reply


