from pathlib import Path
import json
from model_layer.ai.gemini_client import call_gemini

# =====================================================
#                     PATHS
# =====================================================

BASE_DIR = Path(__file__).resolve().parents[2]
RAG_DIR = BASE_DIR / "rag_data"

# =====================================================
#                     CONSTANTS
# =====================================================

TOPIC_MAP = {
    "Event-Driven Programming": "event_driven",
    "Object-Oriented Programming": "oop",
    "Procedural Programming": "procedural",
    "OOP": "oop",
}

# =====================================================
#                     LOADERS
# =====================================================

def _load_rag(topic: str) -> str:
    key = TOPIC_MAP.get(topic)
    if not key:
        return ""
    path = RAG_DIR / f"{key}.txt"
    return path.read_text(encoding="utf-8") if path.exists() else ""

# =====================================================
#                     HELPERS
# =====================================================

def _safe_json_parse(text: str) -> dict | None:
    if not text:
        return None

    try:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start == -1 or end == -1:
            return None

        data = json.loads(text[start:end])

        if (
            isinstance(data, dict)
            and "question" in data
            and "options" in data
            and "correct_index" in data
            and isinstance(data["options"], list)
            and len(data["options"]) == 4
            and isinstance(data["correct_index"], int)
            and 0 <= data["correct_index"] < 4
        ):
            return data

    except Exception:
        return None

    return None

# =====================================================
#                     CORE
# =====================================================

def generate_ai_quiz(topic: str, level: str) -> dict:
    """
    Generate quiz WITH correct answer returned.
    Backend can store correct_index & correct_answer safely.
    """

    rag = _load_rag(topic)

    prompt = f"""
أنت مدرس BTEC IT.

أنشئ سؤال اختيار من متعدد (MCQ) للتدريب فقط.

الموضوع: {topic}
المستوى: {level}

القواعد:
- سؤال واحد فقط
- 4 خيارات فقط
- إجابة صحيحة واحدة
- لا تضف شرح
- لا نص إضافي خارج JSON

Context:
{rag}

أعد النتيجة بصيغة JSON فقط:
{{
  "question": "",
  "options": ["", "", "", ""],
  "correct_index": 0
}}
"""

    text = call_gemini(prompt)
    quiz = _safe_json_parse(text)

    if quiz:
        idx = quiz["correct_index"]
        return {
            "question": quiz["question"],
            "options": quiz["options"],
            "correct_index": idx,
            # ✅ النص الصريح للإجابة الصحيحة (للتخزين في DB)
            "correct_answer": quiz["options"][idx],
        }

    # ---------- Fallback ----------
    fallback_options = [
        "مفهوم غير متعلق",
        "مفهوم أساسي في الموضوع",
        "مفهوم من درس آخر",
        "إجابة غير صحيحة",
    ]

    return {
        "question": "ما هو المفهوم الأساسي في هذا الدرس؟",
        "options": fallback_options,
        "correct_index": 1,
        "correct_answer": fallback_options[1],
    }
