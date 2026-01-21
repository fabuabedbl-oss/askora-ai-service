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


def _load_rag(topic: str) -> str:
    key = TOPIC_MAP.get(topic)
    if not key:
        raise ValueError(f"Unsupported topic: {topic}")

    file_path = RAG_DIR / f"{key}.txt"
    return file_path.read_text(encoding="utf-8")


def generate_explanation(topic: str, level: str = "Beginner") -> str:
    rag = _load_rag(topic)

    if level == "Beginner":
        style = "اشرح الفكرة بأسلوب مبسط جداً مع أمثلة من الحياة اليومية."
    elif level == "Intermediate":
        style = "اشرح بمستوى متوسط مع توضيح المصطلحات الأساسية."
    else:
        style = "اشرح بمستوى متقدم مع ربط المفاهيم البرمجية ببعضها."

    prompt = f"""
أنت مدرس BTEC IT في الأردن.

المستوى: {level}

قواعد:
- اشرح بالعربية الفصحى المبسطة.
- استخدم المصطلحات التقنية بالإنجليزية بين قوسين عند الحاجة.
- لا تستخدم Markdown أو نقاط.

الموضوع:
{topic}

Context:
{rag}

تعليمات الأسلوب:
{style}
"""

    text = call_gemini(prompt)
    return text.strip() if text else "MODEL_ERROR"
