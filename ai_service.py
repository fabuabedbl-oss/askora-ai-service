import os
import json
import re
from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai

# ----------------------------
# Environment
# ----------------------------
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise RuntimeError("Missing API key")

client = genai.Client(api_key=API_KEY)

app = FastAPI(title="Askora AI Service", version="1.2.0")

# ----------------------------
# Topic mapping (for backend)
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

def load_topic_context(topic_name: str) -> str:
    internal = TOPIC_NAME_MAP.get(topic_name)
    if not internal:
        return ""
    path = TOPIC_TO_FILE.get(internal)
    if not path or not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()

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
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text or ""

# ----------------------------
# Prompts
# ----------------------------
SYSTEM_RULES = """
أنت مدرس لمنصة Askora مخصص لطلاب BTEC IT في الأردن.
اشرح بالعربية الفصحى المبسطة.
ضع المصطلحات التقنية بالإنجليزية بين قوسين عند أول ذكر.
التزم بالتوبك الحالي فقط.
ممنوع ذكر AI أو مصادر أو أنظمة داخلية.
"""

LESSON_SCHEMA = """
أخرج JSON فقط:
{
  "site_greeting": "",
  "title": "",
  "overview": "",
  "key_terms": [{"term_ar":"","term_en":"","definition_ar":""}],
  "example": {"description_ar":"","code":"","explain_ar":""},
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

REJECT_TEXT = "سؤالك خارج نطاق هذا الدرس في Askora. افتح درسًا مناسبًا أو اسأل ضمن موضوع الصفحة الحالية."

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
    context = load_topic_context(req.topic)
    if not context:
        return {"error": "Topic not found"}

    prompt = f"""
{SYSTEM_RULES}
{LESSON_SCHEMA}

السياق:
\"\"\"
{context}
\"\"\"

اشرح التوبك شرحًا عامًا ومتكاملًا بدون أسئلة أو كويز.
"""
    return json.loads(strip_code_fences(generate(prompt)))

@app.post("/practice")
def practice(req: TopicRequest):
    context = load_topic_context(req.topic)
    if not context:
        return {"error": "Topic not found"}

    prompt = f"""
{SYSTEM_RULES}
{PRACTICE_SCHEMA}

السياق:
\"\"\"
{context}
\"\"\"

أنشئ سؤال تدريب واحد مناسب للمبتدئين.
"""
    return json.loads(strip_code_fences(generate(prompt)))

@app.post("/quiz")
def quiz(req: TopicRequest):
    context = load_topic_context(req.topic)
    if not context:
        return {"error": "Topic not found"}

    prompt = f"""
{SYSTEM_RULES}
{QUIZ_SCHEMA}

السياق:
\"\"\"
{context}
\"\"\"

أنشئ سؤال اختيار من متعدد واحد.
"""
    data = json.loads(strip_code_fences(generate(prompt)))
    data["grading_note"] = "Correct answer = 100%, wrong = 0%"
    return data

@app.post("/chat")
def chat(req: ChatRequest):
    context = load_topic_context(req.topic)
    if not context:
        return {"scope": "OUT_OF_SCOPE", "answer_ar": REJECT_TEXT, "related_to_topic": False}

    prompt = f"""
{SYSTEM_RULES}
{CHAT_SCHEMA}

السياق:
\"\"\"
{context}
\"\"\"

سؤال الطالب:
\"\"\"
{req.message}
\"\"\"

إذا السؤال مرتبط أجبীৱ، وإذا لا استخدم نص الرفض حرفيًا.
"""
    return json.loads(strip_code_fences(generate(prompt)))
