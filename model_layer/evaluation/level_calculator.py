import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
RULES_PATH = BASE_DIR / "data" / "level_rules.json"

with open(RULES_PATH, encoding="utf-8") as f:
    LEVEL_RULES = json.load(f)


def calculate_level(avg_score: float) -> str:
    """
    Determine student level based on average score.

    Rules are loaded from level_rules.json
    """
    for level, rule in LEVEL_RULES.items():
        if rule["min"] <= avg_score < rule["max"]:
            return level

    # Fallback safety
    return "Advanced"
