from fastapi import FastAPI
from pydantic import BaseModel
from ai_service import explain_topic, generate_exercise, generate_quiz, chat

app = FastAPI(title="Askora AI Service")


class TopicRequest(BaseModel):
    topic: str


class ChatRequest(BaseModel):
    topic: str
    question: str


@app.post("/explain")
def explain(req: TopicRequest):
    return {"answer": explain_topic(req.topic)}


@app.post("/exercise")
def exercise(req: TopicRequest):
    return {"answer": generate_exercise(req.topic)}


@app.post("/quiz")
def quiz(req: TopicRequest):
    return {"answer": generate_quiz(req.topic)}


@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    return {"answer": chat(req.topic, req.question)}
