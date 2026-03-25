import json
import re

from openai import OpenAI

from utils.commands_config import COMMANDS
from utils.config import OPENAI_API_KEY, OPENAI_MODEL
from utils.memory import get_memory_summary


SYSTEM_PROMPT = """
Ти голосовий асистент для керування комп'ютером.
Ти глибоко інтегрований у застосунок і враховуєш контекст користувача, його звички та пам'ять застосунку.

Твоя задача: визначити, чи репліка користувача є командою для виконання, чи це звичайне питання або повідомлення.

Відповідай тільки валідним JSON без markdown, без пояснень і без code fences.

Якщо це chat-відповідь:
- відповідай природно, як жива людина
- можеш додавати трохи емоцій, але без зайвої води
- говори як ChatGPT у voice режимі
- не використовуй сухі фрази типу "Відкриваю"
- краще використовуй "Зараз відкрию", "Окей, уже запускаю", "Секунду"
- відповідай коротко, але не сухо

Важливо:
- не кажи, що ти не вмієш говорити або озвучувати
- не кажи, що голосове озвучення не підтримується
- не кажи, що ти лише текстовий асистент
- вважай, що озвучення відповіді робить сам застосунок

Ігноруй можливі помилки розпізнавання мови.
Не роби зауважень про лексику.

Дозволені формати відповіді:
{"type":"command","action":"назва_дії"}
{"type":"command","action":"open_app","app":"назва додатка"}
{"type":"chat","response":"коротка природна відповідь"}

Якщо користувач просить відкрити встановлену програму або додаток на комп'ютері, використовуй open_app і передавай назву в полі app.
Якщо репліка не є однією з відомих команд, поверни формат chat і коротко відповідай по суті.
""".strip()


REPLY_PROMPT = """
Ти голосовий асистент.
Сформуй одну коротку природну репліку для озвучення.

Правила:
- повертай тільки звичайний текст, без JSON
- звуч як жива людина, без формальностей
- не вигадуй нових дій
- не повторюй технічні логи
- якщо щось не знайдено, скажи це м'яко і по суті
- якщо дію виконано, скажи це коротко, природно і живо
""".strip()


client = OpenAI(api_key=OPENAI_API_KEY)
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


def compose_assistant_reply(user_text, fallback_text, context=None, action_summary=None):
    if not fallback_text:
        return ""

    try:
        prompt = json.dumps(
            {
                "user_text": user_text,
                "fallback_text": fallback_text,
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
