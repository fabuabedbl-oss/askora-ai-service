import random
import json
from pathlib import Path

# ===== AI =====
from model_layer.ai.explanation_generator import generate_explanation
from model_layer.ai.feedback_generator import generate_exercise_feedback
from model_layer.ai.chat_guard import chat_with_topic_guard

# ===== Evaluation =====
from model_layer.evaluation.exercise_evaluator import evaluate_exercise
from model_layer.evaluation.quiz_evaluator import evaluate_quiz

# ===== Paths =====
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "model_layer" / "data"

# ===== Load Data =====
with open(DATA_DIR / "exercises.json", encoding="utf-8") as f:
    EXERCISES = json.load(f)

with open(DATA_DIR / "quizzes.json", encoding="utf-8") as f:
    QUIZZES = json.load(f)


# =====================================================
#                     EXPLANATION
# =====================================================

def explain_topic(topic: str, level: str | None = None) -> str:
    """
    تستخدمها endpoint: /explain
    لو الطالب Visitor → level = Beginner
    """
    level = level or "Beginner"
    return generate_explanation(topic, level)


# =====================================================
#                     EXERCISES
# =====================================================

def generate_exercise_item(topic: str, level: str | None = None) -> dict:
    """
    ترجع سؤال تدريب واحد فقط
    """
    level = level or "Beginner"

    topic_data = EXERCISES.get(topic)
    if not topic_data:
        return {"error": "NO_EXERCISES_FOR_TOPIC"}

    level_items = topic_data.get(level) or topic_data.get("Beginner", [])
    if not level_items:
        return {"error": "NO_EXERCISES_FOR_LEVEL"}

    item = random.choice(level_items)

    return {
        "id": item["id"],
        "question": item["question"],
        "instruction": "اكتب إجابتك بأسلوبك الخاص، لا تعتمد على الحفظ."
    }


def evaluate_exercise_answer(
    topic: str,
    exercise_id: int,
    student_answer: str
) -> dict:
    """
    تقييم إجابة التدريب + feedback
    """
    topic_data = EXERCISES.get(topic)
    if not topic_data:
        return {"error": "NO_EXERCISES_FOR_TOPIC"}

    target_item = None
    for level_items in topic_data.values():
        for item in level_items:
            if item["id"] == exercise_id:
                target_item = item
                break
        if target_item:
            break

    if not target_item:
        return {"error": "EXERCISE_NOT_FOUND"}

    expected_points = target_item.get("expected_points", [])

    eval_result = evaluate_exercise(student_answer, expected_points)

    feedback = generate_exercise_feedback(
        topic=topic,
        student_answer=student_answer,
        covered_points=eval_result["covered_points"],
        missing_points=eval_result["missing_points"]
    )

    return {
        "score_5": eval_result["score_5"],
        "is_correct": eval_result["is_correct"],
        "covered_points": eval_result["covered_points"],
        "missing_points": eval_result["missing_points"],
        "feedback": feedback
    }


# =====================================================
#                     QUIZZES
# =====================================================

def generate_quiz_item(topic: str, level: str | None = None) -> dict:
    """
    ترجع سؤال كويز MCQ بدون الإجابة الصحيحة
    """
    level = level or "Beginner"

    topic_data = QUIZZES.get(topic)
    if not topic_data:
        return {"error": "NO_QUIZZES_FOR_TOPIC"}

    level_items = topic_data.get(level) or topic_data.get("Beginner", [])
    if not level_items:
        return {"error": "NO_QUIZZES_FOR_LEVEL"}

    item = random.choice(level_items)

    return {
        "id": item["id"],
        "question": item["question"],
        "options": item["options"]
    }


def evaluate_quiz_answer(
    topic: str,
    quiz_id: int,
    student_choice_index: int
) -> dict:
    """
    تقييم إجابة الكويز
    """
    topic_data = QUIZZES.get(topic)
    if not topic_data:
        return {"error": "NO_QUIZZES_FOR_TOPIC"}

    target_item = None
    for level_items in topic_data.values():
        for item in level_items:
            if item["id"] == quiz_id:
                target_item = item
                break
        if target_item:
            break

    if not target_item:
        return {"error": "QUIZ_NOT_FOUND"}

    eval_result = evaluate_quiz(
        student_choice_index,
        target_item["correct_index"]
    )

    return {
        "score_5": eval_result["score_5"],
        "is_correct": eval_result["is_correct"]
    }


# =====================================================
#                       CHAT
# =====================================================

def chat(topic: str, question: str) -> str:
    """
    شات محكوم بالتوبك
    - داخل التوبك → جواب
    - خارج التوبك → اعتذار ثابت
    """
    return chat_with_topic_guard(topic, question)
