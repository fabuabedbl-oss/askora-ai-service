from typing import List, Dict


def evaluate_quiz(
    student_choice_index: int,
    correct_index: int,
    options: List[str],
    explanation: str
) -> Dict:
    """
    Quiz evaluation logic (deterministic).

    - Correct:
        feedback = ✅
        explanation = why the answer is correct
    - Incorrect:
        feedback = ❌
        explanation = correct answer + why it is correct
    """

    is_correct = student_choice_index == correct_index

    student_text = (
        options[student_choice_index]
        if 0 <= student_choice_index < len(options)
        else None
    )

    correct_text = (
        options[correct_index]
        if 0 <= correct_index < len(options)
        else None
    )

    if is_correct:
        final_explanation = explanation
        feedback = "✅"
        score = 5
    else:
        final_explanation = (
            f"إجابتك غير صحيحة. الخيار الصحيح هو: «{correct_text}».\n"
            f"{explanation}"
        )
        feedback = "❌"
        score = 0

    return {
        "score_5": score,
        "is_correct": is_correct,
        "student_choice": {
            "index": student_choice_index,
            "text": student_text,
        },
        "correct_answer": {
            "index": correct_index,
            "text": correct_text,
        },
        "feedback": feedback,
        "explanation": final_explanation,
    }
