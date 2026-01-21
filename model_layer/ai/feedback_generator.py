from model_layer.ai.gemini_client import call_gemini


def generate_exercise_feedback(
    topic: str,
    student_answer: str,
    covered_points: list,
    missing_points: list,
) -> str:
    prompt = f"""
أنت مدرس BTEC IT.

قواعد:
- اكتب تعليقاً تعليمياً مشجعاً.
- وضّح ما هو الجيد وما يحتاج تحسين.
- لا تذكر درجات.

الموضوع: {topic}

إجابة الطالب:
{student_answer}

نقاط مغطاة:
{covered_points}

نقاط ناقصة:
{missing_points}
"""

    text = call_gemini(prompt)
    if text:
        return text.strip()

    if not missing_points:
        return "إجابتك ممتازة وتغطي النقاط الأساسية."
    return "إجابتك جيدة، حاول توضيح: " + "، ".join(missing_points)
