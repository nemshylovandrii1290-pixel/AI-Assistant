from openai import OpenAI
import json

from utils.commands_config import COMMANDS
from utils.config import OPENAI_API_KEY, OPENAI_MODEL

client = OpenAI(api_key=OPENAI_API_KEY)

conversation = []

def _build_system_prompt():
  command_examples = []
  for action, data in COMMANDS.items():
    examples = ", ".join(data["examples"])
    command_examples.append(f'- "{action}": {data["description"]}. Приклади: {examples}')

  joined_examples = "\n".join(command_examples)

  return f"""
Ти голосовий AI-асистент.
Твоя задача: визначити, чи є репліка користувача командою для виконання, чи це звичайне питання/повідомлення.

Відповідай тільки валідним JSON без markdown, без пояснень і без code fences.

Дозволені дії команд:
{joined_examples}

Дозволені формати відповіді:
{{"type":"command","action":"назва_дії"}}
{{"type":"command","action":"open_app","app":"назва додатка"}}
{{"type":"chat","response":"текст відповіді користувачу"}}

Якщо користувач просить відкрити встановлену програму або додаток на комп'ютері, використовуй open_app і передавай назву в полі app.
Якщо репліка не є однією з відомих команд, поверни формат chat і коротко відповідай по суті.
"""


def _extract_text(response):
  if not response.output:
    return ""

  parts = []
  for item in response.output:
    for content in getattr(item, "content", []):
      text_value = getattr(content, "text", None)
      if text_value:
        parts.append(text_value)

  return "".join(parts).strip()


def ask_ai(text):
  global conversation

  conversation.append({
    "role": "user",
    "content": text
  })

  response = client.responses.create(
    model=OPENAI_MODEL,
    input=[
      {"role": "system", "content": _build_system_prompt()},
      *conversation
    ]
  )

  reply = _extract_text(response)

  conversation.append({
    "role": "assistant",
    "content": reply
  })

  if len(conversation) > 20:
    conversation = conversation[-20:]

  try:
    return json.loads(reply)
  except json.JSONDecodeError:
    return {
      "type": "chat",
      "response": reply or "Не вдалося обробити відповідь."
    }
