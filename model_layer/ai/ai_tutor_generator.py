from pathlib import Path
from typing import List, Optional
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
        return ""
    path = RAG_DIR / f"{key}.txt"
    return path.read_text(encoding="utf-8") if path.exists() else ""

def generate_ai_tutor(
    topic: str,
    level: str = "Beginner",
    focus_points: Optional[List[str]] = None
) -> str:
    rag = _load_rag(topic)
    focus_text = "، ".join(focus_points) if focus_points else "المفهوم الأساسي في هذا الدرس"

    prompt = f"""
أنت مدرس BTEC IT تعمل كمدرّس مساعد.

الموضوع: {topic}
المستوى: {level}
المفاهيم التي أخطأ فيها الطالب: {focus_text}

المطلوب:
1. شرح مبسط يركّز فقط على هذه المفاهيم
2. مثال واحد واضح
3. سؤال إرشادي واحد
4. تلميحات بدون إعطاء الحل

قواعد:
- لا تذكر الحل
- لا تذكر درجة
- لا تستخدم Markdown
- لا تشرح الدرس كاملاً

Context:
{rag}
"""

    text = call_gemini(prompt)
    return text.strip() if text else f"شرح مبسط حول: {focus_text}."
