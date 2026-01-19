import os
from dotenv import load_dotenv
from pathlib import Path
import google.generativeai as genai

# تحميل متغيرات البيئة
load_dotenv()

# إعداد Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

# Mapping بين اسم التوبك من الفرونت وملف RAG
TOPIC_MAP = {
    "Event Driven Programming": "event_driven"
}

BASE_DIR = Path(__file__).resolve().parent
RAG_DIR = BASE_DIR / "rag_data"


def load_rag(topic_name: str) -> str:
    topic_key = TOPIC_MAP.get(topic_name)
    if not topic_key:
        raise ValueError("Unknown topic")

    rag_file = RAG_DIR / f"{topic_key}.txt"
    return rag_file.read_text(encoding="utf-8")


def call_gemini(prompt: str) -> str:
    response = model.generate_content(prompt)
    return response.text


def explain_topic(topic_name: str) -> str:
    rag = load_rag(topic_name)

    prompt = f"""
You are a teacher for Level 2 IT students.
Explain "{topic_name}" in Arabic.
Keep technical terms in English.
Use simple language.

Context:
{rag}

Answer:
"""
    return call_gemini(prompt)


def generate_exercise(topic_name: str) -> str:
    rag = load_rag(topic_name)

    prompt = f"""
Create ONE simple exercise about "{topic_name}".
No coding required.
Arabic language with English technical terms.

Context:
{rag}

Exercise:
"""
    return call_gemini(prompt)


def generate_quiz(topic_name: str) -> str:
    rag = load_rag(topic_name)

    prompt = f"""
Create ONE MCQ about "{topic_name}".
4 options only.
Arabic language with English technical terms.

Context:
{rag}

Question, options, and correct answer:
"""
    return call_gemini(prompt)


def chat(topic_name: str, question: str) -> str:
    rag = load_rag(topic_name)

    prompt = f"""
You are a strict teacher for Level 2 IT.

Topic: {topic_name}

Rules:
- Answer only if the question is related to the topic and level.
- Otherwise reply:
"عذرًا، هذا السؤال خارج نطاق هذا التوبك والمستوى."

Context:
{rag}

Student Question:
{question}

Answer:
"""
    return call_gemini(prompt)
