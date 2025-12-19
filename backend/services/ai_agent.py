# =============================================================================
# services/ai_agent.py
# =============================================================================

from typing import Dict, Any
import logging
import json

from services.gemini_client import call_gemini
from services.wireframe_prompt import build_wireframe_prompt
from services.api_prompt import build_api_prompt

logger = logging.getLogger("ui_agent")


# -----------------------------------------------------------------------------
# 🧱 WIREframe GENERATION (UNCHANGED)
# -----------------------------------------------------------------------------
def generate_wireframe_ai_sync(project: Dict[str, Any]) -> str:
    logger.info("⚡ Generating wireframe HTML for project: %s", project.get("title"))

    prompt = build_wireframe_prompt(project)
    raw_output = call_gemini(prompt)

    raw_lower = raw_output.lower()
    if "<!doctype" in raw_lower or "<html" in raw_lower:
        return raw_output

    # Safety fallback
    return f"<!DOCTYPE html><html><body>{raw_output}</body></html>"


async def generate_wireframe_ai(project: Dict[str, Any]) -> str:
    return generate_wireframe_ai_sync(project)


# -----------------------------------------------------------------------------
# 🔒 SAFE JSON EXTRACTION (NEW – CRITICAL)
# -----------------------------------------------------------------------------
def extract_json_from_text(text: str) -> Dict[str, Any]:
    """
    Extract first valid JSON object from Gemini output
    """
    start = text.find("{")
    end = text.rfind("}") + 1

    if start == -1 or end == -1:
        raise ValueError("No JSON object found in Gemini response")

    json_str = text[start:end]
    return json.loads(json_str)


# -----------------------------------------------------------------------------
# 🚀 API GENERATION FROM UI INTENT (FIXED)
# -----------------------------------------------------------------------------
def generate_apis_from_ui_intent_sync(ui_intent: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("🚀 Generating APIs from UI intent")

    prompt = build_api_prompt(ui_intent)
    raw_output = call_gemini(prompt)
    print("-------Raw Output-------")
    print(raw_output)
    try:
        api_spec = extract_json_from_text(raw_output)  # ✅ FIX
        return api_spec

    except Exception as e:
        logger.error("❌ Gemini returned invalid JSON for API generation")
        logger.error("---- RAW GEMINI OUTPUT ----")
        logger.error(raw_output)
        logger.error("---------------------------")
        raise


async def generate_apis_from_ui_intent(ui_intent: Dict[str, Any]) -> Dict[str, Any]:
    return generate_apis_from_ui_intent_sync(ui_intent)
