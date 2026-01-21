import os
import time
from dotenv import load_dotenv
from google import genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise RuntimeError("Missing GEMINI_API_KEY / GOOGLE_API_KEY")

client = genai.Client(api_key=API_KEY)

# نحاول أكثر من موديل
MODELS = [
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
]


def call_gemini(prompt: str) -> str | None:
    """
    استدعاء آمن لـ Gemini
    يرجع نص أو None في حالة الفشل
    """
    for model in MODELS:
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
            )
            text = getattr(response, "text", None)
            if text:
                return text
        except Exception as e:
            if "503" in str(e):
                time.sleep(1)
                continue
            return None
    return None
