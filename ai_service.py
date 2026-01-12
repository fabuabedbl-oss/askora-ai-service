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

client = None
if API_KEY:
    try:
        client = genai.Client(api_key=API_KEY)
    except Exception:
        client = None

app = FastAPI(title="Askora AI Service", version="FINAL-1.0")

# ----------------------------
# Topic Mapping
# ----------------------------
TOPIC_MAP = {
    "Event-Driven Programming": "event_driven",
    "Object-Oriented Programming (OOP)": "oop",
    "Procedural Programming": "procedural"
}

def load_topic_file(topic):
    key = TOPIC_MAP.get(topic)
    if not key:
        return None
    path = f"rag_data/{key}.txt"
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

# ----------------------------
# Helpers
# ----------------------------
def strip_json(text):
    if not text:
        return None
    text = text.strip()
    text = re.sub(r"^```json", "", text)
    text = re.sub(r"```$", "", text)
    return text.strip()

def try_generate(prompt):
    if not client:
        return None
    try:
        res = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return res.text
    except Exception:
        return None

# ----------------------------
# Models
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
    return {"status": "Askora running"}

@app.get("/health")
def health():
    return {"status": "ok"}

# ---------- LESSON ----------
@app.post("/lesson")
def lesson(req: TopicRequest):
    context = load_topic_file(req.topic)
    if not context:
        return {"error": "Topic not found"}

    prompt = f"""
اشرح هذا الموضوع شرحًا تعليميًا كاملاً وبالعربية:
{context}
أخرج JSON فقط.
"""
    result = try_generate(prompt)

    if result:
        return json.loads(strip_json(result))

    # 🔹 FALLBACK
    return {
        "title": req.topic,
        "overview": context,
        "note": "Static fallback lesson (model unavailable)"
    }

# ---------- PRACTICE ----------
@app.post("/practice")
def practice(req: TopicRequest):
    if not load_topic_file(req.topic):
        return {"error": "Topic not found"}

    prompt = "أنشئ سؤال تدريب واحد فقط وأخرجه JSON"
    result = try_generate(prompt)

    if result:
        return json.loads(strip_json(result))

    return {
        "question_ar": f"اشرح مفهوم {req.topic} باختصار.",
        "answer_ar": "إجابة مفتوحة.",
        "hint_ar": "راجع الشرح أعلاه."
    }

# ---------- QUIZ ----------
@app.post("/quiz")
def quiz(req: TopicRequest):
    if not load_topic_file(req.topic):
        return {"error": "Topic not found"}

    prompt = "أنشئ سؤال اختيار من متعدد وأخرجه JSON"
    result = try_generate(prompt)

    if result:
        return json.loads(strip_json(result))

    return {
        "question_ar": f"ما الهدف من {req.topic}؟",
        "choices": ["تنظيم الكود", "تشغيل النظام", "تصميم الواجهات", "لا شيء"],
        "correct_index": 0,
        "explain_ar": "لأن الهدف الأساسي هو تنظيم منطق البرنامج."
    }

# ---------- CHAT ----------
@app.post("/chat")
def chat(req: ChatRequest):
    context = load_topic_file(req.topic)
    if not context:
        return {
            "scope": "OUT_OF_SCOPE",
            "answer_ar": "الموضوع غير موجود.",
            "related_to_topic": False
        }

    prompt = f"""
السياق:
{context}

سؤال الطالب:
{req.message}

أجب إذا السؤال متعلق، وإلا ارفض.
أخرج JSON فقط.
"""
    result = try_generate(prompt)

    if result:
        return json.loads(strip_json(result))

    # 🔹 FALLBACK CHAT
    return {
        "scope": "IN_SCOPE",
        "answer_ar": f"سؤالك مرتبط بموضوع {req.topic}. سيتم توسيع الإجابة لاحقًا.",
        "related_to_topic": True
    }
