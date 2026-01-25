from model_layer.ai.gemini_client import call_gemini


def generate_exercise_feedback(
    student_answer: str,
    covered_points: list[str],
    missing_points: list[str],
) -> str:
    """
    يولّد Feedback قصير ومباشر على إجابة الطالب فقط:
    - يذكر ما تم تغطيته بشكل صحيح
    - يوضح ما هو ناقص
    - بدون شرح عام للتوبك
    - بدون أمثلة
    - بدون تعليم جديد (هذا دور AI Tutor)
    """

    prompt = f"""
أنت مدرس BTEC IT.

مهمتك:
كتابة تعليق قصير ومباشر على إجابة الطالب فقط.

القواعد:
- لا تشرح الدرس أو التوبك.
- لا تضف معلومات جديدة.
- لا تعطي أمثلة.
- لا تذكر درجات أو تقييم رقمي.
- ركّز فقط على هذه الإجابة.

إجابة الطالب:
{student_answer}

نقاط غطاها الطالب بشكل صحيح:
{covered_points}

نقاط لم يغطها الطالب:
{missing_points}

اكتب تعليقًا تعليميًا مختصرًا من سطرين إلى ثلاثة أسطر كحد أقصى.
"""

    text = call_gemini(prompt)
    if text and text.strip():
        return text.strip()

    # Fallback deterministic feedback
    if not missing_points:
        return "إجابتك جيدة وتغطي جميع النقاط المطلوبة لهذا السؤال."
    if covered_points:
        return (
            "إجابتك صحيحة جزئيًا، لكن تحتاج إلى توضيح: "
            + "، ".join(missing_points)
        )
    return "إجابتك غير كافية لهذا السؤال، حاول التركيز على النقاط الأساسية المطلوبة."
