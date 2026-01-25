import os
import time
from dotenv import load_dotenv
from google import genai

# =====================================================
#                 ENV
# =====================================================

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise RuntimeError("Missing GEMINI_API_KEY / GOOGLE_API_KEY")

client = genai.Client(api_key=API_KEY)

# =====================================================
#                 MODELS
# =====================================================

MODELS = [
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
]

# =====================================================
#                 CALL GEMINI (FIXED)
# =====================================================

def call_gemini(prompt: str):
    """
    Safe Gemini call using google-genai SDK.
    Returns text or None.
    """

    for model in MODELS:
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
            )

            # ✅ الطريقة الصحيحة لاستخراج النص
            if response and hasattr(response, "candidates"):
                candidates = response.candidates
                if candidates:
                    content = candidates[0].content
                    if content and content.parts:
                        text = content.parts[0].text
                        if text:
                            return text.strip()

        except Exception as e:
            msg = str(e).lower()

            if "429" in msg or "quota" in msg or "rate" in msg:
                time.sleep(1)
                continue

            print("[Gemini Error]:", e)
            return None

    return None
