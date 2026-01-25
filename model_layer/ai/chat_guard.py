import json
from pathlib import Path
from typing import Optional, Dict
from model_layer.ai.gemini_client import call_gemini

BASE_DIR = Path(__file__).resolve().parents[2]
RAG_DIR = BASE_DIR / "rag_data"
DATA_DIR = BASE_DIR / "model_layer" / "data"

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
    "criteria", "الكرايتيريا", "المعايير",
    "learning outcomes", "المنهاج", "المقرر",
    "p m d", "pass merit distinction",
    "pass", "merit", "distinction"
]

def _load_rag(topic: str) -> str:
    key = TOPIC_MAP.get(topic)
    if not key:
        raise ValueError("Unsupported topic")
    return (RAG_DIR / f"{key}.txt").read_text(encoding="utf-8")

def _load_topic_criteria(topic: str) -> Optional[Dict]:
    file_path = DATA_DIR / "topic_criteria.json"
    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)
    return data.get(topic)

def _is_criteria_question(question: str) -> bool:
    q = question.lower()
    return any(keyword in q for keyword in CRITERIA_KEYWORDS)

def _extract_topic_from_question(question: str) -> Optional[str]:
    q = question.lower()
    if "event" in q:
        return "Event-Driven Programming"
    if "oop" in q or "object oriented" in q:
        return "Object-Oriented Programming"
    if "procedural" in q:
        return "Procedural Programming"
    return None

def _detect_requested_criteria(question: str) -> str:
    q = question.lower()
    if "pass" in q or " p " in f" {q} ":
        return "P"
    if "merit" in q or " m " in f" {q} ":
        return "M"
    if "distinction" in q or " d " in f" {q} ":
        return "D"
    return "ALL"

def chat_with_topic_guard(topic: str, question: str) -> str:
    if _is_criteria_question(question):
        requested_topic = _extract_topic_from_question(question)
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
            response += "🔹 Pass (P):\n" + "\n".join(
                f"- {item}" for item in criteria_data["criteria"]["P"]
            ) + "\n\n"

        if requested_level in ("M", "ALL"):
            response += "🔹 Merit (M):\n" + "\n".join(
                f"- {item}" for item in criteria_data["criteria"]["M"]
            ) + "\n\n"

        if requested_level in ("D", "ALL"):
            response += "🔹 Distinction (D):\n" + "\n".join(
                f"- {item}" for item in criteria_data["criteria"]["D"]
            )

        return response.strip()

    rag = _load_rag(topic)

    prompt = f"""
أنت مدرس BTEC IT صارم جداً.

إذا كان السؤال خارج موضوع "{topic}"
أجب فقط:
"{OUT_OF_SCOPE_MESSAGE}"

Context:
{rag}

سؤال الطالب:
{question}
"""

    text = call_gemini(prompt)
    if not text:
        return "MODEL_ERROR"

    if OUT_OF_SCOPE_MESSAGE in text:
        return OUT_OF_SCOPE_MESSAGE

    return text.strip()
