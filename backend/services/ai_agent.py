# =============================================================================
# services/ai_agent.py
# =============================================================================

import json
import logging
import requests
from typing import Dict, Any

logger = logging.getLogger("ui_agent")
logger.setLevel(logging.INFO)

if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logger.addHandler(ch)


# -------------------------------------------------------------------
# OLLAMA CONFIG
# -------------------------------------------------------------------
OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2:3b"


# -------------------------------------------------------------------
# PROMPT → GENERATE CLEAN HTML UI/UX PREVIEW
# -------------------------------------------------------------------
PROMPT_TEMPLATE = """
You are a Senior UI/UX Engineer.

TASK:
- Convert the following project JSON into a single HTML wireframe.
- Use clean and minimal HTML5 + inline CSS only (no JS, no external libraries).
- The output must be ONE HTML file.
- Create a separate <section> for each module and page in the JSON.
- Each page should contain only clean form fields (input, textarea, select).
- Include standard pages if missing: Login, Register, Dashboard, Logout.
- Use simple neutral layout: 
    - max-width: 700px
    - margin: 20px auto
    - font-family: Arial
    - minimal borders
- Do NOT add sample data or dummy text.
- Do NOT skip any module/page from the JSON.
- Do NOT add advanced UI elements. Keep everything basic.
- Produce ONLY pure HTML output. No markdown. No explanations. No comments.


PROJECT JSON:
{{project_json}}
"""

# -------------------------------------------------------------------
# MAIN GENERATOR (SYNC)
# -------------------------------------------------------------------
def generate_wireframe_ai_sync(project: Dict[str, Any]) -> Dict[str, Any]:

    logger.info("⚡ Generating HTML UI preview for project: %s", project.get("title"))

    prompt = PROMPT_TEMPLATE.format(
        project_json=json.dumps(project, indent=2)
    )
    #print("json",json.dumps(project, indent=2))
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }

    try:
        # Call Ollama
        resp = requests.post(f"{OLLAMA_URL}/api/generate", json=payload)
        body = resp.json()

        # Extract model response
        raw = body.get("response") or body.get("output") or ""

        print("\n===== RAW OLLAMA OUTPUT =====")
        print(raw)
        print("===== END =====\n")

        # Detect HTML content
        if "<html" in raw.lower() or "<!doctype" in raw.lower():
            return raw

        # If model responds with just fragments, still return as HTML
        return raw

    except Exception as e:
        logger.error(f"❌ AI request failed: {str(e)}")
        return {
            "html_preview": "<p style='color:red;'>AI failed to generate preview.</p>"
        }


# -------------------------------------------------------------------
# MAIN GENERATOR (ASYNC WRAPPER)
# -------------------------------------------------------------------
async def generate_wireframe_ai(project: Dict[str, Any]):
    return generate_wireframe_ai_sync(project)
