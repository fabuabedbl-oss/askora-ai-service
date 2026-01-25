def evaluate_exercise(student_answer: str, expected_points: list[str]) -> dict:
    if not student_answer.strip():
        return {
            "score_5": 0,
            "is_correct": False,
            "covered_points": [],
            "missing_points": expected_points,
        }

    answer = student_answer.lower()
    covered, missing = [], []

    for p in expected_points:
        if p.lower() in answer:
            covered.append(p)
        else:
            missing.append(p)

    ratio = len(covered) / max(len(expected_points), 1)

    if ratio == 0:
        score = 1
    elif ratio < 0.4:
        score = 3
    elif ratio < 0.7:
        score = 4
    else:
        score = 5

    return {
        "score_5": score,
        "is_correct": score >= 3,
        "covered_points": covered,
        "missing_points": missing,
    }
