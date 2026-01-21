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
    version="2.3.0",
    description="Adaptive learning backend for BTEC IT"
)


# =====================================================
#                     SCHEMAS
# =====================================================

class TopicRequest(BaseModel):
    topic: str
    level: str | None = None


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


# =====================================================
#                     ROOT
# =====================================================

@app.get("/")
def root():
    return {"status": "Askora AI Service is running"}


# =====================================================
#                     EXPLAIN
# =====================================================

@app.post("/explain")
def explain(data: TopicRequest):
    return {
        "answer": explain_topic(data.topic, data.level)
    }


# =====================================================
#                     EXERCISE
# =====================================================

@app.post("/exercise")
def exercise(data: TopicRequest):
    return generate_exercise_item(data.topic, data.level)


@app.post("/exercise/evaluate")
def exercise_evaluate(data: ExerciseEvalRequest):
    return evaluate_exercise_answer(
        topic=data.topic,
        exercise_id=data.exercise_id,
        student_answer=data.student_answer
    )


# =====================================================
#                     QUIZ
# =====================================================

@app.post("/quiz")
def quiz(data: TopicRequest):
    return generate_quiz_item(data.topic, data.level)


@app.post("/quiz/evaluate")
def quiz_evaluate(data: QuizEvalRequest):
    return evaluate_quiz_answer(
        topic=data.topic,
        quiz_id=data.quiz_id,
        student_choice_index=data.student_choice_index
    )


# =====================================================
#                     CHAT
# =====================================================

@app.post("/chat")
def chat_endpoint(data: ChatRequest):
    return {
        "answer": chat(data.topic, data.question)
    }
