import os
import json
import re
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai

# ============================
# Environment
# ============================
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise RuntimeError("Missing API key")

client = genai.Client(api_key=API_KEY)

app = FastAPI(
    title="Askora AI Service",
    version="1.3.0"
)

# ============================
# Topic Mapping (CRITICAL)
# ============================
# Backend MUST send topic exactly like these keys
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
    internal_key = TOPIC_NAME_MAP.get(topic_name)
    if not internal_key:
        return ""

    path = TOPIC_TO_FILE.get(internal_key)
    if not path or not os.path.exists(path):
        return ""

    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()

# ============================
# Helpers
# ============================
def strip_code_fences(text: str) -> str:
    """
    Removes ```json ``` safely
    """
    if not text:
        return ""
    t = text.strip()
    t = re.sub(r"^```(?:json)?", "", t, flags=re.IGNORECASE).strip()
    t = re.sub(r"```$", "", t).strip()
    return t

def generate(prompt: str) -> dict:
    """
    Generates content and guarantees JSON parsing
    """
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    cleaned = strip_code_fences(response.text or "")

    try:
        return json.loads(cleaned)
    except Exception:
        return {
            "error": "Model returned invalid JSON",
            "raw": cleaned
        }

# ============================
# Prompts (STRICT & CLEAN)
# ============================
SYSTEM_RULES = """
أنت مدرس حقيقي لمنصة Askora مخصص لطلاب BTEC IT في الأردن.

التعليمات:
- اشرح بالعربية الفصحى المبسطة.
- اذكر المصطلحات التقنية بالإنجليزية بين قوسين عند أول ظهور فقط.
- التزم بالتوبك المحدد ولا تخرج عنه.
- الشرح يجب أن يكون طبيعي وكأنه من معلم.
- ممنوع ذكر AI أو prompts أو ملفات أو أنظمة داخلية أو مصادر.
"""

LESSON_SCHEMA = """
أخرج JSON فقط بالشكل التالي:
{
  "site_greeting": "نص ترحيبي قصير باسم Askora",
  "title": "عنوان الدرس",
  "overview": "شرح مفتوح ومفصل",
  "key_terms": [
    {"term_ar":"","term_en":"","definition_ar":""}
  ],
  "example": {
    "description_ar":"",
    "code":"",
    "explain_ar":""
  },
  "out_of_scope_notice": "جملة قصيرة"
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

REJECT_TEXT = (
    "سؤالك خارج نطاق هذا الدرس في Askora. "
    "افتح درسًا مناسبًا أو اسأل ضمن موضوع الصفحة الحالية."
)

# ============================
# API Models
# ============================
class TopicRequest(BaseModel):
    topic: str

class ChatRequest(BaseModel):
    topic: str
    message: str

# ============================
# Endpoints
# ============================
@app.get("/")
def root():
    return {
        "message": "Askora AI Service is running",
        "topics_supported": list(TOPIC_NAME_MAP.keys())
    }

@app.get("/health")
def health():
    return {"status": "ok"}

# ---------- LESSON ----------
@app.post("/lesson")
def lesson(req: TopicRequest):
    context = load_topic_context(req.topic)
    if not context:
        return {"error": "Topic not found", "expected_topics": list(TOPIC_NAME_MAP.keys())}

    prompt = f"""
{SYSTEM_RULES}
{LESSON_SCHEMA}

السياق:
\"\"\"
{context}
\"\"\"

اشرح التوبك شرحًا عامًا ومتكاملًا بدون أي أسئلة أو كويز.
"""
    return generate(prompt)

# ---------- PRACTICE ----------
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

أنشئ سؤال تدريب واحد فقط مناسب للمبتدئين.
"""
    return generate(prompt)

# ---------- QUIZ ----------
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

أنشئ سؤال اختيار من متعدد واحد فقط.
"""
    data = generate(prompt)
    data["grading_rule"] = "correct = 100%, wrong = 0%"
    return data

# ---------- CHAT ----------
@app.post("/chat")
def chat(req: ChatRequest):
    context = load_topic_context(req.topic)
    if not context:
        return {
            "scope": "OUT_OF_SCOPE",
            "answer_ar": REJECT_TEXT,
            "related_to_topic": False
        }

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

إذا السؤال مرتبط بالتوبك أجب.
إذا غير مرتبط استخدم نص الرفض حرفيًا.
"""
    return generate(prompt)
