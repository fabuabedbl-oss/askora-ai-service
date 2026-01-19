from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from ai_service import (
    explain_topic,
    generate_exercise,
    generate_quiz,
    chat_with_guard
)

app = FastAPI(
    title="Askora AI Service",
    version="2.0.0",
    description="AI-powered educational backend for Askora (BTEC IT)"
)

# =========================
# Request Models
# =========================
class TopicRequest(BaseModel):
    topic: str


class ChatRequest(BaseModel):
    topic: str
    question: str


# =========================
# Health
# =========================
@app.get("/")
def root():
    return {"status": "Askora AI Service is running"}


# =========================
# Endpoints
# =========================
@app.post("/explain")
def explain(req: TopicRequest):
    try:
        return {"answer": explain_topic(req.topic)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/exercise")
def exercise(req: TopicRequest):
    try:
        return {"answer": generate_exercise(req.topic)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/quiz")
def quiz(req: TopicRequest):
    try:
        return {"answer": generate_quiz(req.topic)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/chat")
def chat(req: ChatRequest):
    return {"answer": chat_with_guard(req.topic, req.question)}
