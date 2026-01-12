import os
import json
import re
from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai

# ----------------------------
# Setup
# ----------------------------
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise RuntimeError("Missing API key")

client = genai.Client(api_key=API_KEY)

app = FastAPI(title="Askora AI Service", version="1.1.0")

# ----------------------------
# RAG mapping
# ----------------------------
TOPIC_TO_FILE = {
    "event_driven": "rag_data/event_driven.txt",
    "oop": "rag_data/oop.txt",
    "procedural": "rag_data/procedural.txt",
}

def load_context(topic: str) -> str:
    with open(TOPIC_TO_FILE[topic], encoding="utf-8") as f:
        return f.read().strip()

# ----------------------------
# Helpers
# ----------------------------
def clean_json(text: str) -> str:
    t = text.strip()
    t = re.sub(r"^```(?:json)?", "", t)
    t = re.sub(r"```$", "", t)
    return t.strip()

def ask_model(prompt: str) -> dict:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return json.loads(clean_json(response.text))

# ----------------------------
# System rules
# ----------------------------
SYSTEM_RULES = """
أنت مساعد تعليمي لمنصة Askora لطلاب BTEC IT في الأردن.

قواعد:
1) اشرح بالعربية الفصحى المبسطة (مبدئي افتراضيًا).
2) ضع المصطلحات التقنية بالإنجليزية بين قوسين عند أول ذكر.
3) التزم بالتوبك الحالي فقط.
4) مسموح إضافة شرح مفيد ضمن نفس التوبك.
5) ممنوع ذكر أي شيء عن AI أو prompts أو files أو datasets.

صيغة الرفض (استخدمها حرفيًا):
"سؤالك خارج نطاق هذا الدرس في Askora. افتح درسًا مناسبًا أو اسأل ضمن موضوع الصفحة الحالية."
"""

# ----------------------------
# API Models
# ----------------------------
class TopicRequest(BaseModel):
    topic: Literal["event_driven", "oop", "procedural"]

class QuizRequest(BaseModel):
    topic: Literal["event_driven", "oop", "procedural"]
    selected_index: int

class ChatRequest(BaseModel):
    topic: Literal["event_driven", "oop", "procedural"]
    message: str

# ----------------------------
# Endpoints
# ----------------------------
@app.get("/")
def root():
    return {"message": "Askora AI Service is running. Visit /docs for Swagger UI."}

@app.get("/health")
def health():
    return {"status": "ok"}

# ---------- LESSON ----------
@app.post("/lesson")
def lesson(req: TopicRequest):
    prompt = f"""
{SYSTEM_RULES}

اشرح الدرس فقط بدون practice أو quiz.

السياق:
{load_context(req.topic)}

أخرج JSON يحتوي:
- site_greeting
- title
- overview
- key_terms
- example
- out_of_scope_notice
"""
    return ask_model(prompt)

# ---------- PRACTICE ----------
@app.post("/practice")
def practice(req: TopicRequest):
    prompt = f"""
{SYSTEM_RULES}

أنشئ سؤال تدريب واحد فقط مع:
- question_ar
- answer_ar
- hint_ar

السياق:
{load_context(req.topic)}

أخرج JSON فقط.
"""
    return ask_model(prompt)

# ---------- QUIZ ----------
@app.post("/quiz")
def quiz(req: QuizRequest):
    prompt = f"""
{SYSTEM_RULES}

أنشئ سؤال اختيار من متعدد (4 خيارات) مع:
- question_ar
- choices
- correct_index
- explain_ar

السياق:
{load_context(req.topic)}

أخرج JSON فقط.
"""
    data = ask_model(prompt)

    return {
        "correct": req.selected_index == data["correct_index"],
        "correct_index": data["correct_index"],
        "explain_ar": data["explain_ar"]
    }

# ---------- CHAT ----------
@app.post("/chat")
def chat(req: ChatRequest):
    prompt = f"""
{SYSTEM_RULES}

السياق:
{load_context(req.topic)}

سؤال الطالب:
{req.message}

إذا السؤال مرتبط بالتوبك أجب.
إذا غير مرتبط استخدم صيغة الرفض.

أخرج JSON:
- scope
- answer_ar
- related_to_topic
"""
    return ask_model(prompt)
