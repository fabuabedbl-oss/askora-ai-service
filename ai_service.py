import os
import json
import re
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai

# =========================
# Environment
# =========================
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise RuntimeError("Missing API key")

client = genai.Client(api_key=API_KEY)

app = FastAPI(
    title="Askora AI Service",
    version="1.5.2",
    description="AI-powered educational backend for Askora (BTEC IT - Jordan)"
)

# =========================
# Topic mapping
# =========================
TOPIC_MAP = {
    "Event-Driven Programming": "event_driven",
    "Object-Oriented Programming (OOP)": "oop",
    "Procedural Programming": "procedural"
}

TOPIC_FILES = {
    "event_driven": "rag_data/event_driven.txt",
    "oop": "rag_data/oop.txt",
    "procedural": "rag_data/procedural.txt"
}

def load_context(topic: str) -> str:
    key = TOPIC_MAP.get(topic)
    if not key:
        return ""
    path = TOPIC_FILES.get(key)
    if not path or not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()

# =========================
# Helpers
# =========================
def clean_json(text: str) -> dict:
    if not text:
        raise HTTPException(status_code=500, detail="Empty model response")

    text = text.strip()
    text = re.sub(r"^```(?:json)?", "", text)
    text = re.sub(r"```$", "", text)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail=f"Invalid JSON returned from model:\n{text}"
        )

def generate(prompt: str) -> str:
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",  # ✅ WORKING & SUPPORTED
            contents=prompt
        )
        return response.text or ""
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Model generation failed: {str(e)}"
        )

# =========================
# Prompt rules & schemas
# =========================
SYSTEM_RULES = """
أنت مدرس لمنصة Askora مخصص لطلاب BTEC IT في الأردن.
اشرح بالعربية الفصحى المبسطة وبأسلوب تعليمي طبيعي.
اذكر المصطلحات التقنية بالإنجليزية بين قوسين عند أول ذكر فقط.
ممنوع ذكر AI أو prompts أو ملفات أو أنظمة داخلية.
"""

LESSON_SCHEMA = """
أخرج JSON فقط بالشكل التالي:
{
  "site_greeting": "",
  "title": "",
  "overview": "",
  "key_terms": [
    {"term_ar":"","term_en":"","definition_ar":""}
  ],
  "example": {
    "description_ar":"",
    "code":"",
    "explain_ar":""
  },
  "out_of_scope_notice": ""
}
"""

PRACTICE_SCHEMA = """
أخرج JSON فقط:
{
  "question_ar": "",
  "answer_ar": "",
  "hint_ar": ""
}
"""

QUIZ_SCHEMA = """
أخرج JSON فقط:
{
  "question_ar": "",
  "choices": ["", "", "", ""],
  "correct_index": 0,
  "explain_ar": ""
}
"""

CHAT_SCHEMA = """
أخرج JSON فقط:
{
  "scope": "IN_SCOPE أو OUT_OF_SCOPE",
  "answer_ar": "",
  "related_to_topic": true/false
}
"""

REJECT_TEXT = "سؤالك خارج نطاق هذا الدرس في Askora. الرجاء الالتزام بموضوع الصفحة الحالية."

# =========================
# Request models
# =========================
class TopicRequest(BaseModel):
    topic: str

class ChatRequest(BaseModel):
    topic: str
    message: str

# =========================
# Health
# =========================
@app.get("/")
def root():
    return {"status": "Askora AI Service is running"}

@app.get("/health")
def health():
    return {"status": "ok"}

# =========================
# Endpoints
# =========================
@app.post("/lesson")
def lesson(req: TopicRequest):
    context = load_context(req.topic)
    if not context:
        raise HTTPException(status_code=404, detail="Topic not found")

    prompt = f"""
{SYSTEM_RULES}
{LESSON_SCHEMA}

المحتوى:
\"\"\"
{context}
\"\"\"

اشرح الدرس شرحًا تعليميًا متكاملًا.
"""
    return clean_json(generate(prompt))

@app.post("/practice")
def practice(req: TopicRequest):
    context = load_context(req.topic)
    if not context:
        raise HTTPException(status_code=404, detail="Topic not found")

    prompt = f"""
{SYSTEM_RULES}
{PRACTICE_SCHEMA}

اعتمادًا على هذا المحتوى:
\"\"\"
{context}
\"\"\"
"""
    return clean_json(generate(prompt))

@app.post("/quiz")
def quiz(req: TopicRequest):
    context = load_context(req.topic)
    if not context:
        raise HTTPException(status_code=404, detail="Topic not found")

    prompt = f"""
{SYSTEM_RULES}
{QUIZ_SCHEMA}

اعتمادًا على هذا المحتوى:
\"\"\"
{context}
\"\"\"
"""
    return clean_json(generate(prompt))

@app.post("/chat")
def chat(req: ChatRequest):
    context = load_context(req.topic)
    if not context:
        return {
            "scope": "OUT_OF_SCOPE",
            "answer_ar": REJECT_TEXT,
            "related_to_topic": False
        }

    prompt = f"""
{SYSTEM_RULES}
{CHAT_SCHEMA}

المحتوى:
\"\"\"
{context}
\"\"\"

سؤال الطالب:
\"\"\"
{req.message}
\"\"\"
"""
    return clean_json(generate(prompt))
