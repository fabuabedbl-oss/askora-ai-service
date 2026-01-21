def evaluate_quiz(student_choice_index: int, correct_index: int) -> dict:
    is_correct = student_choice_index == correct_index
    return {
        "score_5": 5 if is_correct else 0,
        "is_correct": is_correct,
    }
