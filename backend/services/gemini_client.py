# =============================================================================
# services/gemini_client.py
# =============================================================================

import os
import logging
import requests
from typing import Optional

logger = logging.getLogger("gemini_client")
logger.setLevel(logging.INFO)

if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logger.addHandler(ch)

# -------------------------------------------------------------------
# CONFIG
# -------------------------------------------------------------------

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("❌ GEMINI_API_KEY not set")

GEMINI_MODEL = "models/gemini-flash-latest"
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/"
    f"{GEMINI_MODEL}:generateContent"
)


def call_gemini(prompt: str, max_tokens: int = 8192) -> str:
    """
    Send prompt to Gemini and return raw text output
    """

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": max_tokens
        }
    }

    try:
        response = requests.post(
            f"{GEMINI_URL}?key={GEMINI_API_KEY}",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=1200
        )
        response.raise_for_status()
        body = response.json()

        raw = (
            body.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )

        logger.info("✅ Gemini response received")
        return raw.strip()

    except Exception as e:
        logger.error(f"❌ Gemini call failed: {str(e)}")
        raise
