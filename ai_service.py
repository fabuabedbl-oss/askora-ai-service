import os
import json
import re
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai

# ----------------------------
# Environment
# ----------------------------
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=API_KEY) if API_KEY else None

app = FastAPI(title="Askora AI Service", version="1.3.1")

# ----------------------------
# Topic mapping (IMPORTANT)
# ----------------------------
TOPIC_NAME_MAP = {
    "Event-Driven Programming": "event_driven",
    "Object-Oriented Programming (OOP)": "oop",
    "Procedural Programming": "procedural"
}

TOPIC_TO_FILE = {
    "event_driven": "rag_data/event_driven.txt",
    "oop": "rag_data/oop.txt",
    "procedural": "rag_data/procedural.txt",
}

# ----------------------------
# Helpers
# ----------------------------
def strip_code_fences(text: str) -> str:
    t = (text or "").strip()
    if t.startswith("```"):
        t = re.sub(r"^```(?:json)?\s*", "", t, flags=re.IGNORECASE)
        t = re.sub(r"\s*```$", "", t)
    return t.strip()

def generate(prompt: str) -> str:
    if not client:
        raise RuntimeError("Model unavailable")
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt
    )
    return response.text or ""

# ----------------------------
# Static fallback lessons (IMPORTANT)
# ----------------------------
STATIC_LESSONS = {
    "event_driven": {
        "site_greeting": "مرحبًا بك في Askora",
        "title": "Event-Driven Programming",
        "overview": (
            "البرمجة المعتمدة على الأحداث هي أسلوب برمجي يعتمد على تنفيذ الأوامر "
            "عند حدوث حدث معين مثل ضغط زر أو إدخال المستخدم. بدلاً من تنفيذ الكود "
            "بشكل متسلسل، يبقى البرنامج في حالة انتظار حتى يحدث تفاعل، ثم يستجيب له. "
            "هذا الأسلوب شائع في واجهات المستخدم والتطبيقات التفاعلية."
        ),
        "key_terms": [
            {"term_ar": "الحدث", "term_en": "Event", "definition_ar": "إشارة لحدوث فعل معين"},
            {"term_ar": "معالج الحدث", "term_en": "Event Handler", "definition_ar": "كود ينفذ عند وقوع الحدث"},
            {"term_ar": "مستمع الحدث", "term_en": "Event Listener", "definition_ar": "جزء يراقب حدوث الحدث"},
            {"term_ar": "حلقة الأحداث", "term_en": "Event Loop", "definition_ar": "آلية تنتظر وتدير الأحداث"}
        ],
        "example": {
            "description_ar": "مثال بسيط يوضح الفكرة",
            "code": "print('Button clicked')",
            "explain_ar": "يتم تنفيذ الكود عند حدوث حدث الضغط"
        },
        "out_of_scope_notice": "هذا الدرس يشرح المفهوم العام فقط"
    }
}

# ----------------------------
# API Models
# ----------------------------
class TopicRequest(BaseModel):
    topic: str

class ChatRequest(BaseModel):
    topic: str
    message: str

# ----------------------------
# Endpoints
# ----------------------------
@app.get("/")
def root():
    return {"message": "Askora AI Service is running. Visit /docs"}

@app.post("/lesson")
def lesson(req: TopicRequest):
    internal = TOPIC_NAME_MAP.get(req.topic)
    if not internal:
        return {"error": "Topic not found"}

    try:
        prompt = f"""
اشرح موضوع {req.topic} شرحًا تعليميًا مناسبًا لطلاب BTEC.
أخرج JSON فقط بالشكل التالي:
{{
  "site_greeting": "",
  "title": "",
  "overview": "",
  "key_terms": [],
  "example": {{}},
  "out_of_scope_notice": ""
}}
"""
        return json.loads(strip_code_fences(generate(prompt)))
    except Exception:
        return STATIC_LESSONS.get(internal, {"error": "Lesson unavailable"})

@app.post("/practice")
def practice(req: TopicRequest):
    return {
        "question_ar": "ما المقصود بالحدث في Event-Driven Programming؟",
        "answer_ar": "هو إشارة لحدوث تفاعل معين في النظام",
        "hint_ar": "فكر بتفاعل المستخدم"
    }

@app.post("/quiz")
def quiz(req: TopicRequest):
    return {
        "question_ar": "ما وظيفة Event Handler؟",
        "choices": [
            "مراقبة الأحداث",
            "تنفيذ الكود عند الحدث",
            "إنشاء الواجهة",
            "إيقاف البرنامج"
        ],
        "correct_index": 1,
        "explain_ar": "معالج الحدث ينفذ الكود عند وقوع الحدث"
    }

@app.post("/chat")
def chat(req: ChatRequest):
    internal = TOPIC_NAME_MAP.get(req.topic)
    if not internal:
        return {
            "scope": "OUT_OF_SCOPE",
            "answer_ar": "سؤالك خارج نطاق هذا الدرس في Askora.",
            "related_to_topic": False
        }

    try:
        prompt = f"""
أجب على السؤال التالي ضمن موضوع {req.topic} فقط:
{req.message}
"""
        return {
            "scope": "IN_SCOPE",
            "answer_ar": generate(prompt),
            "related_to_topic": True
        }
    except Exception:
        return {
            "scope": "IN_SCOPE",
            "answer_ar": "الحدث هو إشارة لحدوث تفاعل داخل النظام.",
            "related_to_topic": True
        }
