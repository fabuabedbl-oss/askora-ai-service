from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

# ===================== AI SERVICE =====================

from ai_service import (
    explain_topic,
    generate_exercise_item,
    evaluate_exercise_answer,
    generate_quiz_item,
    evaluate_quiz_answer,
    chat
)

# ===================== LEVEL CALCULATION =====================

from model_layer.evaluation.level_calculator import calculate_level

# ===================== APP INIT =====================

app = FastAPI(
    title="Askora AI Service",
    version="2.4.0",
    description="Adaptive learning backend for BTEC IT"
)

# ===================== REQUEST MODELS =====================

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


# 🔹 NEW: Level API Models
class LevelRequest(BaseModel):
    scores: List[float]


class LevelResponse(BaseModel):
    average_score: float
    level: str

# ===================== ROOT =====================

@app.get("/")
def root():
    return {"status": "Askora AI Service is running"}

# ===================== EXPLANATION =====================

@app.post("/explain")
def explain(data: ExplainRequest):
    return {"answer": explain_topic(data.topic, data.level)}

# ===================== EXERCISES =====================

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

# ===================== QUIZ =====================

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

# ===================== CHAT =====================

@app.post("/chat")
def chat_endpoint(data: ChatRequest):
    return {"answer": chat(data.topic, data.question)}

# ===================== 🔥 LEVEL API (NEW) =====================

@app.post("/student/level", response_model=LevelResponse)
def calculate_student_level(data: LevelRequest):
    """
    Receives all quiz/exercise scores for a student
    and returns:
    - average_score
    - calculated level (Beginner / Intermediate / Advanced)
    """

    if not data.scores:
        avg_score = 0.0
    else:
        avg_score = sum(data.scores) / len(data.scores)

    level = calculate_level(avg_score)

    return {
        "average_score": round(avg_score, 2),
        "level": level
    }
