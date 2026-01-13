import os
import json
import re
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("Missing GEMINI_API_KEY")

client = genai.Client(api_key=API_KEY)

app = FastAPI(
    title="Askora AI Service",
    version="1.6.0",
    description="AI-powered educational backend for Askora (BTEC IT - Jordan)"
)

# =====================
# Topic Mapping
# =====================
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
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

# =====================
# Helpers
# =====================
def clean_json(text: str) -> dict:
    text = re.sub(r"```(?:json)?", "", text).strip()
    text = re.sub(r"```", "", text).strip()
    try:
        return json.loads(text)
    except:
        raise HTTPException(500, "Invalid JSON returned")

def generate(prompt: str) -> str:
    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=prompt
    )
    return response.text

# =====================
# Schemas
# =====================
LESSON_SCHEMA = """
Return JSON only:
{
  "title": "",
  "overview": "",
  "sections": [],
  "example": "",
  "summary": ""
}
"""

CHAT_SCHEMA = """
Return JSON only:
{
  "scope": "IN_SCOPE or OUT_OF_SCOPE",
  "answer": ""
}
"""

# =====================
# Requests
# =====================
class TopicRequest(BaseModel):
    topic: str

class ChatRequest(BaseModel):
    topic: str
    message: str

# =====================
# Endpoints
# =====================
@app.post("/lesson")
def lesson(req: TopicRequest):
    context = load_context(req.topic)
    if not context:
        raise HTTPException(404, "Topic not found")

    prompt = f"""
You are an educational assistant.
Use the following material to generate a structured lesson.

{LESSON_SCHEMA}

Content:
{context}
"""
    return clean_json(generate(prompt))

@app.post("/chat")
def chat(req: ChatRequest):
    context = load_context(req.topic)

    prompt = f"""
Answer the question ONLY if it is related to the topic content.
If not, mark it OUT_OF_SCOPE.

{CHAT_SCHEMA}

Topic content:
{context}

Student question:
{req.message}
"""
    return clean_json(generate(prompt))
