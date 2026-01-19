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
# إعداد Gemini (الموديل المستقر)
# =========================
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("models/gemini-1.0-pro")

# =========================
# Mapping التوبك → ملف RAG
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
أنت مدرس حاسوب لطلاب Level 2 IT.

اشرح التوبك التالي باللغة العربية وبأسلوب مبسط:
"{topic_name}"

- أبقِ المصطلحات التقنية باللغة الإنجليزية
- استخدم فقط المعلومات الموجودة في السياق
- لا تضف أي معلومات من خارج المنهاج

السياق:
{rag}

الشرح:
"""
    return call_gemini(prompt)

# =========================
# تمرين واحد
# =========================
def generate_exercise(topic_name: str) -> str:
    rag = load_rag(topic_name)

    prompt = f"""
أنشئ تمرينًا واحدًا بسيطًا عن:
"{topic_name}"

- بدون كود
- مناسب لطلاب Level 2
- عربي مع مصطلحات تقنية إنجليزية فقط
- اعتمادًا فقط على السياق

السياق:
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
أنشئ سؤال اختيار من متعدد (MCQ) واحد فقط عن:
"{topic_name}"

الشروط:
- 4 خيارات (A, B, C, D)
- إجابة واحدة صحيحة
- مستوى Level 2
- عربي مع مصطلحات تقنية إنجليزية

السياق:
{rag}

الصيغة:
Question:
...

Options:
A)
B)
C)
D)

Correct Answer:
"""
    return call_gemini(prompt)

# =========================
# شات مع حارس التوبك
# =========================
def chat(topic_name: str, question: str) -> str:
    rag = load_rag(topic_name)

    prompt = f"""
أنت مدرس صارم لطلاب Level 2 IT.

التوبك: {topic_name}

القواعد:
- أجب فقط إذا كان السؤال متعلقًا بالتوبك والمستوى
- إذا لم يكن كذلك، أجب حرفيًا:
"عذرًا، هذا السؤال خارج نطاق هذا التوبك والمستوى المطلوب."
- استخدم فقط السياق

السياق:
{rag}

سؤال الطالب:
{question}

الإجابة:
"""
    return call_gemini(prompt)
