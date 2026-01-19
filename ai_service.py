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
# استدعاء Gemini (بشكل آمن)
# =========================
def call_gemini(prompt: str) -> str:
    response = client.models.generate_content(
        model="gemini-1.5-pro",
        contents=prompt
    )

    # استخراج النص بطريقة متوافقة مع google-genai
    if hasattr(response, "text") and response.text:
        return response.text

    if hasattr(response, "candidates"):
        return response.candidates[0].content.parts[0].text

    return "حدث خطأ أثناء توليد الإجابة."

# =========================
# شرح التوبك
# =========================
def explain_topic(topic_name: str) -> str:
    rag = load_rag(topic_name)

    prompt = f"""
You are a teacher for Level 2 IT students.

Explain "{topic_name}" in Arabic.
Use simple language suitable for school students.
Keep important technical terms in English.

Use ONLY the following context:

{rag}

Answer in Arabic:
"""
    return call_gemini(prompt)

# =========================
# تمرين واحد
# =========================
def generate_exercise(topic_name: str) -> str:
    rag = load_rag(topic_name)

    prompt = f"""
You are a teacher for Level 2 IT students.

Create ONE simple exercise about "{topic_name}".
No coding required.
Arabic language with English technical terms.

Context:
{rag}

Exercise:
"""
    return call_gemini(prompt)

# =========================
# سؤال اختيار من متعدد
# =========================
def generate_quiz(topic_name: str) -> str:
    rag = load_rag(topic_name)

    prompt = f"""
You are a teacher for Level 2 IT students.

Create ONE multiple-choice question (MCQ) about "{topic_name}".

Rules:
- Exactly 4 options (A, B, C, D)
- Only ONE correct answer
- Simple Level 2 difficulty
- Arabic with English technical terms

Context:
{rag}

Output format:
Question:
<question>

Options:
A) ...
B) ...
C) ...
D) ...

Correct Answer:
<letter>
"""
    return call_gemini(prompt)

# =========================
# شات مع حارس التوبك
# =========================
def chat(topic_name: str, question: str) -> str:
    rag = load_rag(topic_name)

    prompt = f"""
You are a strict but helpful teacher for Level 2 IT students.

Topic: {topic_name}
Level: Level 2 IT

Rules:
- Answer ONLY if the question is related to this topic and level.
- If not related, reply exactly with:
"عذرًا، هذا السؤال خارج نطاق هذا التوبك والمستوى المطلوب."
- Use simple Arabic and keep technical terms in English.
- Use ONLY the provided context.

Context:
{rag}

Student Question:
{question}

Answer in Arabic:
"""
    return call_gemini(prompt)
