import os
import json
from typing import Literal, Optional, Dict, Any

from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise RuntimeError("Missing API key. Put GEMINI_API_KEY (or GOOGLE_API_KEY) in .env")

client = genai.Client(api_key=API_KEY)

app = FastAPI(title="Askora AI Service", version="1.0.0")


# ----------------------------
# Curriculum (RAG) utilities
# ----------------------------
TOPIC_TO_FILE = {
    "event_driven": "rag_data/event_driven.txt",
    "oop": "rag_data/oop.txt",
    "procedural": "rag_data/procedural.txt",
}

def load_topic_context(topic: str) -> str:
    path = TOPIC_TO_FILE.get(topic)
    if not path or not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


# ----------------------------
# Prompts
# ----------------------------
SYSTEM_RULES = """أنت مساعد تعليمي لمنصة Askora مخصص لطلاب BTEC IT في الأردن.
القواعد الصارمة:
1) اشرح بالعربية الفصحى المبسطة، وأضف المصطلحات التقنية بالإنجليزية بين قوسين عند الحاجة.
2) ممنوع الخروج عن محتوى "السياق" المرفق. إذا لم تجد الإجابة داخل السياق، ارفض بأدب.
3) لا تخمّن ولا تضف معلومات عامة من خارج السياق.
4) إذا كان سؤال المستخدم خارج الموضوع الحالي، أعد رسالة رفض محددة.

صيغة الرفض (استخدمها حرفيًا):
"سؤالك خارج نطاق هذا الدرس في Askora. افتح درسًا مناسبًا أو اسأل ضمن موضوع الصفحة الحالية."
"""

# JSON-only output schema to keep backend integration easy
JSON_SCHEMA_INSTRUCTIONS = """أخرج الإجابة بصيغة JSON فقط وبدون أي نص خارجه.
مفاتيح JSON المطلوبة حسب نوع الطلب:

A) عند طلب "شرح الدرس" (lesson_pack):
{
  "site_greeting": "نص ترحيبي قصير باسم Askora",
  "title": "عنوان الدرس",
  "overview": "شرح مختصر (5-8 أسطر)",
  "key_terms": [{"term_ar":"", "term_en":"", "definition_ar":""}],
  "example": {"description_ar":"", "code":"", "explain_ar":""},
  "practice": {"question_ar":"", "answer_ar":"", "hint_ar":""},
  "quiz": {
    "question_ar":"",
    "choices":["","", "", ""],
    "correct_index": 0,
    "explain_ar":""
  },
  "out_of_scope_notice": "جملة قصيرة تذكّر أن Askora ملتزم بالسياق"
}

B) عند طلب "شات" (chat):
{
  "scope": "IN_SCOPE أو OUT_OF_SCOPE",
  "answer_ar": "الإجابة أو رسالة الرفض",
  "related_to_topic": true/false
}

التزم بالمفاتيح والأسماء كما هي.
"""


def generate_with_gemini(prompt: str) -> str:
    # Using a modern model. If it fails, we can switch to another available one.
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text or ""


# ----------------------------
# API models
# ----------------------------
Level = Literal["beginner", "intermediate", "advanced"]

class LessonRequest(BaseModel):
    topic: Literal["event_driven", "oop", "procedural"]
    level: Level = "beginner"

class ChatRequest(BaseModel):
    topic: Literal["event_driven", "oop", "procedural"]
    level: Level = "beginner"
    message: str


# ----------------------------
# Endpoints
# ----------------------------
@app.get("/health")
def health():
    return {"status": "ok", "service": "askora-ai"}


@app.post("/lesson_pack")
def lesson_pack(req: LessonRequest):
    context = load_topic_context(req.topic)
    if not context:
        return {
            "error": "Topic context not found",
            "topic": req.topic
        }

    level_guidance = {
        "beginner": "استخدم شرحًا مبسطًا جدًا وأمثلة سهلة وكلمات قليلة التعقيد.",
        "intermediate": "استخدم شرحًا متوسطًا مع مثال عملي واضح وسؤال تدريب مناسب.",
        "advanced": "استخدم شرحًا أعمق قليلًا مع مثال أقوى وسؤال تدريب يتطلب تفكير."
    }[req.level]

    prompt = f"""
{SYSTEM_RULES}

{JSON_SCHEMA_INSTRUCTIONS}

السياق (هذا هو المنهاج المسموح فقط):
\"\"\"
{context}
\"\"\"

المطلوب:
- أنشئ lesson_pack كامل للموضوع المحدد.
- التزم بتوجيه المستوى: {level_guidance}
- ضع عنوانًا واضحًا.
- مثال الكود: بايثون (Python) فقط وبسيط.
- اجعل الترحيب يبدأ باسم Askora.

أعد JSON فقط.
"""
    raw = generate_with_gemini(prompt).strip()

    # Try parsing JSON; if model returns fenced json, strip fences.
    cleaned = raw
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        # sometimes "json\n{...}"
        cleaned = cleaned.replace("json\n", "", 1).strip()

    try:
        data = json.loads(cleaned)
        return data
    except Exception:
        # Fallback: return raw for debugging (during development)
        return {"error": "Invalid JSON from model", "raw": raw}


@app.post("/chat")
def chat(req: ChatRequest):
    context = load_topic_context(req.topic)
    if not context:
        return {"scope": "OUT_OF_SCOPE", "answer_ar": "الموضوع غير موجود.", "related_to_topic": False}

    prompt = f"""
{SYSTEM_RULES}

{JSON_SCHEMA_INSTRUCTIONS}

السياق (هذا هو المنهاج المسموح فقط):
\"\"\"
{context}
\"\"\"

رسالة الطالب:
\"\"\"
{req.message}
\"\"\"

المطلوب:
1) إذا كان السؤال يمكن الإجابة عنه من داخل السياق، أجب بإجابة عربية مختصرة وواضحة.
2) إذا كان خارج السياق أو يحتاج معلومات غير موجودة، استخدم صيغة الرفض حرفيًا.

أعد JSON بصيغة chat فقط.
"""
    raw = generate_with_gemini(prompt).strip()

    cleaned = raw
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.replace("json\n", "", 1).strip()

    try:
        data = json.loads(cleaned)
        return data
    except Exception:
        return {"scope": "OUT_OF_SCOPE", "answer_ar": "حصل خطأ في قراءة المخرجات.", "related_to_topic": False, "raw": raw}
