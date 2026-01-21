from pathlib import Path
from model_layer.ai.gemini_client import call_gemini

BASE_DIR = Path(__file__).resolve().parents[2]
RAG_DIR = BASE_DIR / "rag_data"

TOPIC_MAP = {
    "Event-Driven Programming": "event_driven",
    "Object-Oriented Programming": "oop",
    "Procedural Programming": "procedural",
    "OOP": "oop",
}

OUT_OF_SCOPE_MESSAGE = (
    "عذرًا، هذا السؤال خارج نطاق هذا التوبك. "
    "يرجى طرح سؤال متعلق بالموضوع الحالي."
)


def _load_rag(topic: str) -> str:
    key = TOPIC_MAP.get(topic)
    if not key:
        raise ValueError("Unsupported topic")

    return (RAG_DIR / f"{key}.txt").read_text(encoding="utf-8")


def chat_with_topic_guard(topic: str, question: str) -> str:
    """
    - إذا السؤال خارج التوبك → رد ثابت
    - إذا داخل التوبك → يجاوب من الـ RAG
    """

    rag = _load_rag(topic)

    prompt = f"""
أنت مدرس BTEC IT صارم جداً.

مهمتك:
- تحديد هل السؤال متعلق بالموضوع أم لا.

القواعد (مهمة جداً):
- إذا كان السؤال غير متعلق بالموضوع التالي:
  "{topic}"
  يجب أن يكون الرد حرفياً فقط:
  "{OUT_OF_SCOPE_MESSAGE}"

- إذا كان السؤال متعلق بالموضوع:
  أجب عليه باستخدام المعلومات من الـ Context فقط.
  لا تضف معلومات من خارج السياق.

قواعد اللغة:
- أجب بالعربية الفصحى المبسطة.
- لا تستخدم الإنجليزية إلا للمصطلحات التقنية فقط.

Context:
{rag}

سؤال الطالب:
{question}
"""

    text = call_gemini(prompt)
    if text is None:
        return "MODEL_ERROR"

    text = text.strip()

    # حماية إضافية (لو المودل حاول يتفلسف)
    if OUT_OF_SCOPE_MESSAGE in text:
        return OUT_OF_SCOPE_MESSAGE

    return text
