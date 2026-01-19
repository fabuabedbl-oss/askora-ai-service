import os
import time
from pathlib import Path
from dotenv import load_dotenv
from google import genai

# =========================
# Environment
# =========================
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise RuntimeError("Missing GEMINI_API_KEY")

client = genai.Client(api_key=API_KEY)

# =========================
# Topic Mapping
# =========================
TOPIC_MAP = {
    "Event Driven Programming": "event_driven",
    "Object Oriented Programming": "oop",
    "Procedural Programming": "procedural"
}

BASE_DIR = Path(__file__).resolve().parent
RAG_DIR = BASE_DIR / "rag_data"

def load_rag(topic: str) -> str:
    key = TOPIC_MAP.get(topic)
    if not key:
        raise ValueError("Topic not supported")

    file_path = RAG_DIR / f"{key}.txt"
    if not file_path.exists():
        raise ValueError("RAG file missing")

    return file_path.read_text(encoding="utf-8")

# =========================
# Gemini Models (الصحيحة)
# =========================
MODELS = [
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash"
]

def call_gemini(prompt: str) -> str:
    for model in MODELS:
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt
            )
            return response.text or ""
        except Exception as e:
            if "503" in str(e):
                time.sleep(1)
                continue
            break
    raise RuntimeError("Gemini unavailable")

# =========================
# Business Logic
# =========================
def explain_topic(topic: str) -> str:
    rag = load_rag(topic)

    prompt = f"""
You are a teacher for BTEC IT students.

Explain the topic in Arabic.
Use simple academic language.
Mention technical terms in English only when needed.

Context:
{rag}
"""
    return call_gemini(prompt)


def generate_exercise(topic: str) -> str:
    rag = load_rag(topic)

    prompt = f"""
Create ONE simple practice question.
Arabic language.
No programming required.

Context:
{rag}
"""
    return call_gemini(prompt)


def generate_quiz(topic: str) -> str:
    rag = load_rag(topic)

    prompt = f"""
Create ONE multiple choice question.
4 options.
Mention the correct answer clearly.

Context:
{rag}
"""
    return call_gemini(prompt)


def chat_with_guard(topic: str, question: str) -> str:
    rag = load_rag(topic)

    prompt = f"""
You are a strict instructor.

Rules:
- If the question is unrelated, answer exactly:
"عذرًا، هذا السؤال خارج نطاق هذا التوبك."

Context:
{rag}

Question:
{question}
"""
    return call_gemini(prompt)
