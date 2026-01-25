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

ALLOWED_LEVELS = ["Beginner", "Intermediate", "Advanced"]


def _load_rag(topic: str) -> str:
    key = TOPIC_MAP.get(topic)
    if not key:
        return ""
    path = RAG_DIR / f"{key}.txt"
    return path.read_text(encoding="utf-8") if path.exists() else ""


def generate_explanation(topic: str, level: str = "Beginner") -> str:
    if level not in ALLOWED_LEVELS:
        level = "Beginner"

    rag = _load_rag(topic)

    if level == "Beginner":
        style = "اشرح الفكرة بأسلوب مبسط جداً مع أمثلة من الحياة اليومية وتجنب المصطلحات المعقدة."
    elif level == "Intermediate":
        style = "اشرح بمستوى متوسط مع توضيح المصطلحات وربطها بأمثلة برمجية بسيطة."
    else:
        style = "اشرح بمستوى متقدم مع ربط المفاهيم ببعضها وتوضيح الاستخدام العملي."

    prompt = f"""
أنت مدرس Pearson BTEC Level 2 IT في الأردن.

الموضوع: {topic}
المستوى: {level}

قواعد:
- الشرح بالعربية الفصحى المبسطة
- المصطلحات التقنية بالإنجليزية بين قوسين عند الحاجة
- لا تستخدم Markdown
- لا تذكر درجات أو تقييم
- التزم بالمنهاج فقط

Context:
{rag}

أسلوب الشرح:
{style}
"""

    text = call_gemini(prompt)
    if text and text.strip():
        return text.strip()

    return rag[:800] if rag else "سيتم شرح هذا المفهوم بشكل مبسط في هذا الدرس."
