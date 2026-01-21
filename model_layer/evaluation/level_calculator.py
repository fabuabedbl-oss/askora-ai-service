def calculate_level(avg_score: float) -> str:
    if avg_score < 2:
        return "Beginner"
    elif avg_score < 4:
        return "Intermediate"
    return "Advanced"
