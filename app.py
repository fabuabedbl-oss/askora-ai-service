from fastapi import FastAPI
from pydantic import BaseModel

from ai_service import (
    explain_topic,
    generate_exercise_item,
    evaluate_exercise_answer,
    generate_quiz_item,
    evaluate_quiz_answer,
    chat
)

app = FastAPI(
    title="Askora AI Service",
    version="2.4.0",
    description="Adaptive learning backend for BTEC IT"
)


class ExplainRequest(BaseModel):
    topic: str
    level: str | None = None


class TopicRequest(BaseModel):
    topic: str
    level: str | None = None
    use_ai: bool | None = False


class ExerciseEvalRequest(BaseModel):
    topic: str
    exercise_id: int
    student_answer: str


class QuizEvalRequest(BaseModel):
    topic: str
    quiz_id: int
    student_choice_index: int


class ChatRequest(BaseModel):
    topic: str
    question: str


@app.get("/")
def root():
    return {"status": "Askora AI Service is running"}


@app.post("/explain")
def explain(data: ExplainRequest):
    return {"answer": explain_topic(data.topic, data.level)}


@app.post("/exercise")
def exercise(data: TopicRequest):
    return generate_exercise_item(
        data.topic,
        data.level,
        bool(data.use_ai)
    )


@app.post("/exercise/evaluate")
def exercise_evaluate(data: ExerciseEvalRequest):
    return evaluate_exercise_answer(
        data.topic,
        data.exercise_id,
        data.student_answer
    )


@app.post("/quiz")
def quiz(data: TopicRequest):
    return generate_quiz_item(
        data.topic,
        data.level,
        bool(data.use_ai)
    )


@app.post("/quiz/evaluate")
def quiz_evaluate(data: QuizEvalRequest):
    return evaluate_quiz_answer(
        data.topic,
        data.quiz_id,
        data.student_choice_index
    )


@app.post("/chat")
def chat_endpoint(data: ChatRequest):
    return {"answer": chat(data.topic, data.question)}
