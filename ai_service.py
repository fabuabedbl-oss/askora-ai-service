import os
from dotenv import load_dotenv
from pathlib import Path
import google.generativeai as genai

# =========================
# تحميل متغيرات البيئة
# =========================
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is not set in .env file")

# =========================
# إعداد Gemini (الطريقة الصحيحة)
# =========================
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# =========================
# Mapping التوبكس
# =========================
TOPIC_MAP = {
    "Event Driven Programming": "event_driven"
}

BASE_DIR = Path(__file__).resolve().parent
RAG_DIR = BASE_DIR / "rag_data"

# =========================
# تحميل RAG
# =========================
def load_rag(topic_name: str) -> str:
    topic_key = TOPIC_MAP.get(topic_name)
    if not topic_key:
        raise ValueError("Unknown topic")

    rag_file = RAG_DIR / f"{topic_key}.txt"
    if not rag_file.exists():
        raise FileNotFoundError(f"RAG file not found: {rag_file}")

    return rag_file.read_text(encoding="utf-8")

# =========================
# استدعاء Gemini
# =========================
def call_gemini(prompt: str) -> str:
    response = model.generate_content(prompt)
    return response.text

# =========================
# شرح التوبك
# =========================
def explain_topic(topic_name: str) -> str:
    rag = load_rag(topic_name)

    prompt = f"""
أنت مدرس IT لطلاب Level 2.

اشرح موضوع "{topic_name}" باللغة العربية.
استخدم لغة بسيطة.
اترك المصطلحات التقنية المهمة باللغة الإنجليزية.

استخدم فقط المعلومات التالية:

{rag}

الإجابة:
"""
    return call_gemini(prompt)

# =========================
# تمرين
# =========================
def generate_exercise(topic_name: str) -> str:
    rag = load_rag(topic_name)

    prompt = f"""
أنشئ تمرين واحد بسيط عن "{topic_name}".
بدون كود.
عربي مع مصطلحات إنجليزية.

المحتوى:
{rag}

التمرين:
"""
    return call_gemini(prompt)

# =========================
# سؤال MCQ
# =========================
def generate_quiz(topic_name: str) -> str:
    rag = load_rag(topic_name)

    prompt = f"""
أنشئ سؤال اختيار من متعدد واحد عن "{topic_name}".

- 4 خيارات
- إجابة صحيحة واحدة
- مستوى Level 2

المحتوى:
{rag}

الصيغة:
Question:
Options:
Correct Answer:
"""
    return call_gemini(prompt)

# =========================
# Chat Guard
# =========================
def chat(topic_name: str, question: str) -> str:
    rag = load_rag(topic_name)

    prompt = f"""
أنت مدرس صارم.

أجب فقط إذا كان السؤال ضمن "{topic_name}" ومستوى Level 2.
إذا لا، أجب بالنص التالي فقط:
"عذرًا، هذا السؤال خارج نطاق هذا التوبك والمستوى المطلوب."

المحتوى:
{rag}

السؤال:
{question}

الإجابة:
"""
    return call_gemini(prompt)
