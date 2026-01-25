import random
import json
from pathlib import Path

# ===================== AI MODULES =====================

from model_layer.ai.explanation_generator import generate_explanation
from model_layer.ai.exercise_generator import generate_ai_exercise
from model_layer.ai.ai_tutor_generator import generate_ai_tutor
from model_layer.ai.feedback_generator import generate_exercise_feedback
from model_layer.ai.quiz_generator import generate_ai_quiz
from model_layer.ai.chat_guard import chat_with_topic_guard

# ===================== EVALUATION =====================

from model_layer.evaluation.exercise_evaluator import evaluate_exercise
from model_layer.evaluation.quiz_evaluator import evaluate_quiz

# ===================== PATHS & DATA =====================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "model_layer" / "data"

with open(DATA_DIR / "exercises.json", encoding="utf-8") as f:
    EXERCISES = json.load(f)

with open(DATA_DIR / "quizzes.json", encoding="utf-8") as f:
    QUIZZES = json.load(f)

# ===================== MEMORY (LAST FAILED) =====================

# per-topic memory (sufficient for Swagger & graduation project)
LAST_FAILED_EXERCISE: dict[str, int] = {}

# ===================== EXPLANATION =====================

def explain_topic(topic: str, level: str | None = None) -> str:
    """
    شرح الدرس الكامل حسب المستوى (AI Explanation)
    """
    return generate_explanation(topic, level or "Beginner")

# ===================== EXERCISES =====================

def generate_exercise_item(
    topic: str,
    level: str | None = None,
    use_ai: bool = False
) -> dict:
    """
    use_ai = False → سؤال رسمي من بنك الأسئلة (يُحسب)
    use_ai = True  → AI Tutor (شرح + مثال + تلميحات) غير محسوب
    """

    level = level or "Beginner"

    # -------- 1️⃣ OFFICIAL QUESTION (COUNTED) --------
    if not use_ai:
        topic_data = EXERCISES.get(topic, {})
        level_items = topic_data.get(level) or topic_data.get("Beginner", [])

        if level_items:
            item = random.choice(level_items)
            return {
                "id": item["id"],
                "question": item["question"],
                "instruction": "اكتب إجابتك بأسلوبك الخاص، لا تعتمد على الحفظ.",
                "source": "question_bank",
                "counted": True
            }

        return {
            "id": None,
            "question": "لا توجد تمارين متاحة لهذا الموضوع حالياً.",
            "instruction": "راجع الشرح ثم أعد المحاولة لاحقًا.",
            "source": "empty_bank",
            "counted": False
        }

    # -------- 2️⃣ AI TUTOR (SUPPORT ONLY) --------
    last_id = LAST_FAILED_EXERCISE.get(topic)
    focus_points = None

    if last_id is not None:
        for items in EXERCISES.get(topic, {}).values():
            for it in items:
                if it["id"] == last_id:
                    focus_points = it.get("expected_points", [])
                    break

    tutor_text = generate_ai_tutor(topic, level, focus_points)

    return {
        "id": None,
        "question": tutor_text,
        "instruction": (
            "هذا محتوى تعليمي مخصص للمساعدة في المفاهيم التي أخطأت فيها. "
            "هذا الجزء غير محسوب في التقييم."
        ),
        "source": "ai_generated",
        "counted": False
    }

# ===================== EXERCISE EVALUATION =====================

def evaluate_exercise_answer(
    topic: str,
    exercise_id: int,
    student_answer: str
) -> dict:
    """
    تقييم إجابة تمرين رسمي + feedback
    """

    for items in EXERCISES.get(topic, {}).values():
        for item in items:
            if item["id"] == exercise_id:
                result = evaluate_exercise(
                    student_answer,
                    item.get("expected_points", [])
                )

                # حفظ آخر تمرين ضعيف
                if result["score_5"] < 4:
                    LAST_FAILED_EXERCISE[topic] = exercise_id

                feedback = generate_exercise_feedback(
                    student_answer,
                    result["covered_points"],
                    result["missing_points"]
                )

                return {
                    "score_5": result["score_5"],
                    "is_correct": result["is_correct"],
                    "covered_points": result["covered_points"],
                    "missing_points": result["missing_points"],
                    "feedback": feedback
                }

    return {"error": "EXERCISE_NOT_FOUND"}

# ===================== QUIZ =====================

def generate_quiz_item(
    topic: str,
    level: str | None = None,
    use_ai: bool = False
) -> dict:
    level = level or "Beginner"

    if not use_ai:
        items = QUIZZES.get(topic, {}).get(level, [])
        if items:
            q = random.choice(items)
            return {
                "id": q["id"],
                "question": q["question"],
                "options": q["options"],
                "source": "question_bank"
            }

        return {
            "id": None,
            "question": "لا توجد أسئلة كويز حالياً.",
            "options": [],
            "source": "empty_bank"
        }

    quiz = generate_ai_quiz(topic, level)
    return {
        "id": None,
        "question": quiz.get("question"),
        "options": quiz.get("options") or [],
        "source": "ai_generated"
    }

def evaluate_quiz_answer(
    topic: str,
    quiz_id: int,
    student_choice_index: int
) -> dict:
    for items in QUIZZES.get(topic, {}).values():
        for q in items:
            if q["id"] == quiz_id:
                return evaluate_quiz(student_choice_index, q["correct_index"])

    return {"error": "QUIZ_NOT_FOUND"}

# ===================== CHAT =====================

def chat(topic: str, question: str) -> str:
    return chat_with_topic_guard(topic, question)
