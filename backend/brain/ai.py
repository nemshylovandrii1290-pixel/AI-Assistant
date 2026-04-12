import json
import re
import os
import sys
from dotenv import load_dotenv

from openai import OpenAI

from backend.utils.commands_config import COMMANDS
from backend.utils.config import OPENAI_MODEL
from backend.utils.memory import get_memory_summary


SYSTEM_PROMPT = """
Ти голосовий асистент на ім'я Едіт для керування комп'ютером.
Завжди відповідай тільки українською мовою.
Ніколи не використовуй російську або англійську.
Завжди говори від жіночого роду: "я відкрила", "я знайшла", "я зробила".

Тон:
- короткий
- впевнений
- природний
- без води

Твоє завдання: визначити, чи це команда для дії, чи звичайне повідомлення.
Відповідай тільки валідним JSON без markdown і без пояснень.

Дозволені формати:
{"type":"command","action":"назва_дії"}
{"type":"command","action":"open_app","app":"назва додатка"}
{"type":"chat","response":"коротка природна відповідь"}

Якщо користувач просить відкрити встановлений додаток або програму, використовуй open_app.
Якщо це не команда, поверни chat і відповідай коротко та по суті.
""".strip()


REPLY_PROMPT = """
Ти голосовий асистент Едіт.

Сформуй одну коротку природну репліку для озвучення.

Правила:
- тільки звичайний текст, без JSON
- тільки українська
- тільки жіночий рід
- коротко, впевнено і природно
- не вигадуй нових дій
- якщо щось не знайдено, скажи м'яко
- якщо дію виконано, скажи коротко і живо
""".strip()


STREAM_REPLY_PROMPT = """
Ти real-time голосовий асистент Едіт.
Завжди відповідай тільки українською.
Завжди говори від жіночого роду.
Відповідай коротко, природно і без зайвої води.
Не використовуй JSON.
Не описуй внутрішні кроки або інструменти.
""".strip()

def get_app_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

env_path = os.path.join(get_app_dir(), ".env")
load_dotenv(env_path)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
conversation = []


def _command_examples():
    lines = []
    for action, data in COMMANDS.items():
        examples = ", ".join(data["examples"])
        lines.append(f'- "{action}": {data["description"]}. Приклади: {examples}')
    return "\n".join(lines)


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


def _memory_context(context):
    return json.dumps(
        {
            "runtime_context": context or {},
            "memory": get_memory_summary(),
        },
        ensure_ascii=False,
    )


def _safe_responses_create(input_items):
    return client.responses.create(
        model=OPENAI_MODEL,
        input=input_items,
    )


def _build_system_prompt(context):
    return (
        f"{SYSTEM_PROMPT}\n\n"
        f"Поточний контекст і пам'ять:\n{_memory_context(context)}\n\n"
        f"Дозволені дії команд:\n{_command_examples()}"
    )


def ask_ai(text, context=None):
    global conversation

    conversation.append({"role": "user", "content": text})

    response = _safe_responses_create(
        [
            {"role": "system", "content": _build_system_prompt(context)},
            *conversation,
        ]
    )

    reply = _extract_text(response)
    conversation.append({"role": "assistant", "content": reply})

    if len(conversation) > 20:
        conversation = conversation[-20:]

    try:
        return json.loads(reply)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", reply, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        return {
            "type": "chat",
            "response": reply or "Щось пішло не так, спробуй ще раз.",
        }


def compose_assistant_reply(
    user_text,
    fallback_text=None,
    context=None,
    action_summary=None,
    action_result=None,
):
    if fallback_text is None and action_result is not None:
        fallback_text = action_result

    if not fallback_text:
        return ""

    if not isinstance(fallback_text, str):
        fallback_text = json.dumps(fallback_text, ensure_ascii=False)

    try:
        prompt = json.dumps(
            {
                "user_text": user_text,
                "fallback_text": fallback_text,
                "action_result": action_result or {},
                "action_summary": action_summary or [],
                "context": context or {},
            },
            ensure_ascii=False,
        )

        response = _safe_responses_create(
            [
                {"role": "system", "content": REPLY_PROMPT},
                {
                    "role": "user",
                    "content": (
                        "Ось що сталося. Сформуй коротку живу репліку для озвучення.\n"
                        f"{prompt}"
                    ),
                },
            ]
        )
        reply = _extract_text(response)
        return reply or fallback_text
    except Exception:
        return fallback_text


def ask_gpt_stream(prompt, context=None):
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    f"{STREAM_REPLY_PROMPT}\n\n"
                    f"Поточний контекст і пам'ять:\n{_memory_context(context)}"
                ),
            },
            {"role": "user", "content": prompt},
        ],
        stream=True,
        temperature=0.7,
    )

    for chunk in response:
        try:
            delta = chunk.choices[0].delta.content
        except (AttributeError, IndexError):
            delta = None
        if delta:
            yield delta


def ask_gpt_text(prompt, context=None):
    return "".join(ask_gpt_stream(prompt, context=context)).strip()
