import os
from dotenv import load_dotenv
from pathlib import Path
from google import genai

# =========================
# تحميل متغيرات البيئة
# =========================
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is not set in .env file")

# =========================
# إنشاء Client رسمي لـ Gemini
# =========================
client = genai.Client(api_key=GEMINI_API_KEY)

# =========================
# Mapping بين التوبك وملف RAG
# (مهم جدًا يكون Capital زي الفرونت)
# =========================
TOPIC_MAP = {
    "Event Driven Programming": "event_driven"
}

BASE_DIR = Path(__file__).resolve().parent
RAG_DIR = BASE_DIR / "rag_data"

# =========================
# تحميل محتوى RAG
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
# استدعاء Gemini (الصيغة الصحيحة)
# =========================
def call_gemini(prompt: str) -> str:
    response = client.models.generate_content(
        model="models/gemini-1.5-pro",
        contents=prompt
    )

    # أمان إضافي
    if not response or not response.text:
        return "حدث خطأ أثناء توليد الإجابة."

    return response.text

# =========================
# شرح التوبك
# =========================
def explain_topic(topic_name: str) -> str:
    rag = load_rag(topic_name)

    prompt = f"""
أنت مدرس لمادة IT لطلاب Level 2.

اشرح موضوع "{topic_name}" باللغة العربية.
استخدم لغة بسيطة تناسب طلاب المدارس.
اترك المصطلحات التقنية المهمة باللغة الإنجليزية.

استخدم فقط المعلومات التالية:

{rag}

الإجابة:
"""
    return call_gemini(prompt)

# =========================
# تمرين واحد
# =========================
def generate_exercise(topic_name: str) -> str:
    rag = load_rag(topic_name)

    prompt = f"""
أنشئ تمرين واحد بسيط عن "{topic_name}".
بدون كود.
اللغة العربية مع المصطلحات التقنية بالإنجليزي.

المحتوى:
{rag}

التمرين:
"""
    return call_gemini(prompt)

# =========================
# سؤال اختيار من متعدد
# =========================
def generate_quiz(topic_name: str) -> str:
    rag = load_rag(topic_name)

    prompt = f"""
أنشئ سؤال اختيار من متعدد (MCQ) واحد عن "{topic_name}".

الشروط:
- 4 خيارات فقط (A, B, C, D)
- إجابة صحيحة واحدة
- مستوى Level 2
- عربي مع مصطلحات إنجليزية

المحتوى:
{rag}

الصيغة:
Question:
...

Options:
A) ...
B) ...
C) ...
D) ...

Correct Answer:
...
"""
    return call_gemini(prompt)

# =========================
# شات مع حارس التوبك
# =========================
def chat(topic_name: str, question: str) -> str:
    rag = load_rag(topic_name)

    prompt = f"""
أنت مدرس صارم ولكن متعاون لطلاب Level 2 IT.

الموضوع: {topic_name}

القواعد:
- أجب فقط إذا كان السؤال ضمن هذا التوبك والمستوى.
- إذا كان خارج النطاق، أجب بالنص التالي فقط:
"عذرًا، هذا السؤال خارج نطاق هذا التوبك والمستوى المطلوب."

استخدم اللغة العربية مع المصطلحات الإنجليزية.
استخدم فقط المحتوى التالي:

{rag}

سؤال الطالب:
{question}

الإجابة:
"""
    return call_gemini(prompt)
