import os
import json
import re
import time
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
    version="1.6.0",
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
            detail="Invalid JSON returned from model"
        )

# =========================
# Model Switching
# =========================
MODELS = [
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash"
]

def generate(prompt: str) -> str:
    for model in MODELS:
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt
            )
            return response.text or ""
        except Exception:
            time.sleep(1)
            continue

    raise HTTPException(
        status_code=503,
        detail="AI service temporarily unavailable"
    )

# =========================
# PROMPT CONTROL (CRITICAL)
# =========================
SYSTEM_RULES = """
أنت مدرس لمنصة Askora مخصص لطلاب BTEC IT في الأردن.

التعليمات الصارمة:
- يجب أن يكون الشرح باللغة العربية الفصحى فقط.
- يُمنع استخدام اللغة الإنجليزية في الشرح أو العناوين أو الفقرات.
- اللغة الإنجليزية مسموحة فقط عند ذكر المصطلحات التقنية بين قوسين عند أول ظهور لها.
- يمنع استخدام Markdown أو التعداد النقطي أو الرموز الخاصة.
- اكتب الشرح على شكل فقرات تعليمية متسلسلة مثل الكتاب.
- لا تذكر أي معلومات تقنية عن الذكاء الاصطناعي أو الأنظمة الداخلية.
"""

LESSON_SCHEMA = """
أخرج JSON فقط بالشكل التالي:
{
  "title": "",
  "content": ""
}
"""

# =========================
# Request Models
# =========================
class TopicRequest(BaseModel):
    topic: str

# =========================
# Endpoints
# =========================
@app.get("/")
def root():
    return {"status": "Askora AI Service is running"}

@app.post("/lesson")
def lesson(req: TopicRequest):
    context = load_context(req.topic)
    if not context:
        raise HTTPException(status_code=404, detail="Topic not found")

    prompt = f"""
{SYSTEM_RULES}
{LESSON_SCHEMA}

المحتوى التالي مكتوب بالعربية ويجب الحفاظ على نفس الأسلوب واللغة:

\"\"\"
{context}
\"\"\"

اكتب شرحًا تفصيليًا بنفس الأسلوب المستخدم في الكتب التعليمية وبنفس طريقة العرض كما في الشرح الأكاديمي، مع الحفاظ على اللغة العربية.
"""

    return clean_json(generate(prompt))
