import json
from pathlib import Path
from model_layer.ai.gemini_client import call_gemini

# =====================================================
#                     PATHS
# =====================================================

BASE_DIR = Path(__file__).resolve().parents[2]
RAG_DIR = BASE_DIR / "rag_data"
DATA_DIR = BASE_DIR / "model_layer" / "data"

# =====================================================
#                     CONSTANTS
# =====================================================

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

CRITERIA_KEYWORDS = [
    "criteria",
    "الكرايتيريا",
    "المعايير",
    "learning outcomes",
    "المنهاج",
    "المقرر",
    "p m d",
    "pass merit distinction",
    "pass",
    "merit",
    "distinction"
]

# =====================================================
#                     LOADERS
# =====================================================

def _load_rag(topic: str) -> str:
    key = TOPIC_MAP.get(topic)
    if not key:
        raise ValueError("Unsupported topic")
    return (RAG_DIR / f"{key}.txt").read_text(encoding="utf-8")


def _load_topic_criteria(topic: str) -> dict | None:
    file_path = DATA_DIR / "topic_criteria.json"
    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)
    return data.get(topic)

# =====================================================
#                     HELPERS
# =====================================================

def _is_criteria_question(question: str) -> bool:
    q = question.lower()
    return any(keyword in q for keyword in CRITERIA_KEYWORDS)


def _extract_topic_from_question(question: str) -> str | None:
    """
    Detects if the student explicitly mentions another topic in the question.
    """
    q = question.lower()

    if "event" in q:
        return "Event-Driven Programming"
    if "oop" in q or "object oriented" in q:
        return "Object-Oriented Programming"
    if "procedural" in q:
        return "Procedural Programming"

    return None


def _detect_requested_criteria(question: str) -> str:
    """
    Detects requested criteria level.
    Returns: "P", "M", "D", or "ALL"
    """
    q = question.lower()

    if "pass" in q or " p " in f" {q} ":
        return "P"
    if "merit" in q or " m " in f" {q} ":
        return "M"
    if "distinction" in q or " d " in f" {q} ":
        return "D"

    return "ALL"

# =====================================================
#                     CHAT CORE
# =====================================================

def chat_with_topic_guard(topic: str, question: str) -> str:
    """
    Chat behavior:
    1️⃣ Criteria question (P/M/D) → deterministic syllabus-based response
    2️⃣ In-topic learning question → RAG-based answer
    3️⃣ Out-of-topic question → fixed rejection
    """

    # =================================================
    # 1️⃣ CRITERIA QUESTIONS (STRICT TOPIC CHECK)
    # =================================================
    if _is_criteria_question(question):
        requested_topic = _extract_topic_from_question(question)

        # إذا الطالب ذكر توبك مختلف عن التوبك الحالي
        if requested_topic and requested_topic != topic:
            return OUT_OF_SCOPE_MESSAGE

        criteria_data = _load_topic_criteria(topic)
        if not criteria_data:
            return OUT_OF_SCOPE_MESSAGE

        requested_level = _detect_requested_criteria(question)

        response = (
            f"هذا الموضوع ضمن {criteria_data['unit']}.\n"
            f"هدف التعلم: {criteria_data['learning_aim']}.\n\n"
        )

        if requested_level in ("P", "ALL"):
            p_items = "\n".join(
                f"- {item}" for item in criteria_data["criteria"]["P"]
            )
            response += f"🔹 Pass (P):\n{p_items}\n\n"

        if requested_level in ("M", "ALL"):
            m_items = "\n".join(
                f"- {item}" for item in criteria_data["criteria"]["M"]
            )
            response += f"🔹 Merit (M):\n{m_items}\n\n"

        if requested_level in ("D", "ALL"):
            d_items = "\n".join(
                f"- {item}" for item in criteria_data["criteria"]["D"]
            )
            response += f"🔹 Distinction (D):\n{d_items}"

        return response.strip()

    # =================================================
    # 2️⃣ NORMAL TOPIC CHAT (RAG)
    # =================================================
    rag = _load_rag(topic)

    prompt = f"""
أنت مدرس BTEC IT صارم جداً.

مهمتك:
- تحديد هل السؤال متعلق بالموضوع أم لا.

القواعد:
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

    # =================================================
    # 3️⃣ SAFETY GUARD (ANTI-HALLUCINATION)
    # =================================================

    # رد صريح خارج النطاق
    if OUT_OF_SCOPE_MESSAGE in text:
        return OUT_OF_SCOPE_MESSAGE

    # تحقق إضافي: هل الرد استخدم مفردات من السياق؟
    topic_keywords = set(rag.lower().split()[:50])

    if not any(word in text.lower() for word in topic_keywords):
        return OUT_OF_SCOPE_MESSAGE

    return text
