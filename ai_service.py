import os
import json
import re
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai

# ----------------------------
# ENV
# ----------------------------
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise RuntimeError("Missing API key")

client = genai.Client(api_key=API_KEY)
app = FastAPI(title="Askora AI Service", version="1.0.0")

# ----------------------------
# TOPIC MAPPING
# ----------------------------
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
    if not os.path.exists(path):
        return ""
    return open(path, "r", encoding="utf-8").read()

# ----------------------------
# HELPERS
# ----------------------------
def clean_json(text: str):
    text = text.strip()
    text = re.sub(r"^```json|```$", "", text)
    return json.loads(text)

def generate(prompt: str):
    try:
        res = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )
        return res.text
    except Exception as e:
        raise HTTPException(500, str(e))

# ----------------------------
# SCHEMAS
# ----------------------------
SYSTEM_RULES = """
أنت مدرس يشرح لطلاب BTEC IT في الأردن.
اشرح بالعربية الفصحى المبسطة.
اذكر المصطلحات الإنجليزية عند أول ذكر فقط.
لا تذكر أي أنظمة داخلية أو مصادر.
"""

LESSON_SCHEMA = """
أخرج JSON فقط:
{
  "title": "",
  "overview": "",
  "key_terms": [{"term_ar":"","term_en":"","definition_ar":""}],
  "example": {"code":"","explain_ar":""},
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

REJECT_TEXT = "سؤالك خارج نطاق هذا الدرس في Askora."

# ----------------------------
# MODELS
# ----------------------------
class TopicRequest(BaseModel):
    topic: str

class ChatRequest(BaseModel):
    topic: str
    message: str

# ----------------------------
# ENDPOINTS
# ----------------------------
@app.post("/lesson")
def lesson(req: TopicRequest):
    context = load_context(req.topic)
    if not context:
        raise HTTPException(404, "Topic not found")

    prompt = f"""
{SYSTEM_RULES}
{LESSON_SCHEMA}

المحتوى:
\"\"\"
{context}
\"\"\"

اشرح الموضوع شرحًا تعليميًا متكاملًا.
"""
    return clean_json(generate(prompt))


@app.post("/practice")
def practice(req: TopicRequest):
    context = load_context(req.topic)
    if not context:
        raise HTTPException(404, "Topic not found")

    prompt = f"""
{SYSTEM_RULES}
{PRACTICE_SCHEMA}

اعتمادًا على هذا المحتوى:
\"\"\"
{context}
\"\"\"

أنشئ سؤال تدريب واحد.
"""
    return clean_json(generate(prompt))


@app.post("/quiz")
def quiz(req: TopicRequest):
    context = load_context(req.topic)
    if not context:
        raise HTTPException(404, "Topic not found")

    prompt = f"""
{SYSTEM_RULES}
{QUIZ_SCHEMA}

اعتمادًا على هذا المحتوى:
\"\"\"
{context}
\"\"\"

أنشئ سؤال اختيار من متعدد واحد.
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
