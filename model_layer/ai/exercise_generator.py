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
        return ""
    file_path = RAG_DIR / f"{key}.txt"
    if not file_path.exists():
        return ""
    return file_path.read_text(encoding="utf-8")

def generate_ai_exercise(topic: str, level: str, focus_point: str) -> str:
    rag = _load_rag(topic)

    prompt = f"""
أنت مدرس BTEC IT في الأردن.

أنشئ سؤال تدريب وصفي واحد فقط.

الموضوع: {topic}
المستوى: {level}
التركيز: {focus_point}

القواعد:
- التزم بمنهاج Pearson BTEC Level 2 Unit 5
- السؤال للتدريب فقط
- لا تذكر الحل
- لا تذكر الدرجة
- السؤال يجب أن يكون واضحاً ومحدداً

Context:
{rag}
"""
    text = call_gemini(prompt)
    return text.strip() if text else f"اشرح مفهوم {focus_point} مع مثال بسيط."
