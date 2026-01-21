def evaluate_exercise(student_answer: str, expected_points: list[str]) -> dict:
    answer_lower = student_answer.lower()

    covered = []
    missing = []

    for point in expected_points:
        if point.strip() == "":
            continue
        if point.lower() in answer_lower:
            covered.append(point)
        else:
            missing.append(point)

    total = max(len(expected_points), 1)
    ratio = len(covered) / total

    # ====== منطق تربوي ======
    # لو الطالب كتب إجابة مفهومة (أكثر من 20 حرف مثلاً)
    # نفترض وجود فهم عام حتى لو المصطلحات ناقصة
    has_conceptual_understanding = len(student_answer.strip()) > 20

    if ratio == 0 and has_conceptual_understanding:
        score = 3   # فهم الفكرة لكن المصطلحات ضعيفة
    elif ratio == 0:
        score = 1
    elif ratio < 0.4:
        score = 3
    elif ratio < 0.7:
        score = 4
    else:
        score = 5

    is_correct = score >= 3

    return {
        "score_5": score,
        "is_correct": is_correct,
        "covered_points": covered,
        "missing_points": missing,
    }
