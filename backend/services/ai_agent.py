# services/ai_agent.py

import json
import re
import logging
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger("ui_agent")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logger.addHandler(ch)

OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3:8b"


# -------------------------------------------------------------------
# 1) NEW UI SCHEMA PROMPT (ONLY PAGES, NO LAYOUT, NO COLORS)
# -------------------------------------------------------------------

PROMPT_TEMPLATE = """
You are a senior UI/UX engineer and a JSON-only generator.

TASK:
• Convert each MODULE into one or more PAGES (pages grouped logically).
• Use module fields → INPUT components.
• Use module actions → BUTTON components.
• Group related actions into sensible pages (example: Login flow → login, otp_verification, register, password_recovery).
• For each input, choose an appropriate inputType (text, email, password, tel, date, number, file, textarea, checkbox, select).
• For each action button, produce an action slug (lowercase, underscore).

IMPORTANT OUTPUT RULES:
• Output ONLY valid JSON — no text, no markdown, no explanation.
• Keep layout, navigation, app_name, colors OUT of the output (backend will add them).
• Structure: nested pages under each module slug; each module can contain multiple page objects.

REQUIRED JSON SCHEMA:

{{
  "pages": {{
    "<module_slug>": {{
      "<page_slug>": {{
        "title": "<Page Title>",
        "description": "<short description (optional)>",
        "components": [
          {{ "type": "input",  "label": "Email",       "name": "email",  "inputType": "email", "required": true }},
          {{ "type": "input",  "label": "Mobile",      "name": "mobile", "inputType": "tel" }},
          {{ "type": "select", "label": "User Type",   "name": "user_type", "options": ["Customer","Restaurant","Delivery","Admin"] }},
          {{ "type": "button", "label": "Send OTP",    "action": "send_otp" }},
          {{ "type": "button", "label": "Login",       "action": "login" }}
        ]
      }}
    }}
  }}
}}

ADDITIONAL GUIDELINES:
• Page slugs and action slugs must be lowercase, use underscore, no spaces.
• If actions belong to a flow (OTP, Login), create separate pages (otp_verification, login, register) rather than dumping everything into a single page.
• Keep components order logical: inputs first, then action buttons.
• If a field looks like email/mobile/password, use respective inputType.
• If an action implies a secondary modal (edit/delete), still represent it as a button component with proper action slug.
• Keep pages minimal and user-friendly: split complex admin modules into a "list" page plus "detail/edit" page.

PROJECT:
{project_json}
"""





# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def slugify(text: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", text.lower()).strip("_")


def safe_json_extract(text: str) -> Optional[Dict[str, Any]]:
    """Extract valid JSON even if AI adds noise."""
    text = text.replace("```", "").strip()

    first = text.find("{")
    last = text.rfind("}")

    if first == -1 or last == -1:
        return None

    try:
        return json.loads(text[first:last + 1])
    except:
        return None


# -------------------------------------------------------------------
# 2) GENERATE UI WITH REAL INPUT + BUTTON COMPONENTS
# -------------------------------------------------------------------

def generate_wireframe_ai_sync(project: Dict[str, Any]) -> Dict[str, Any]:

    logger.info("⚡ Creating REAL UI wireframe for: %s", project.get("title"))

    safe_project = {
        "title": project.get("title"),
        "modules": project.get("modules", []),
    }

    prompt = PROMPT_TEMPLATE.format(
        project_json=json.dumps(safe_project, indent=2)
    )

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "max_tokens": 2000
    }

    # --- CALL LLaMA ---
    try:
        resp = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=120)
        body = resp.json()
        raw = body.get("output") or body.get("response") or json.dumps(body)

    except Exception:
        logger.error("❌ AI request failed, using fallback UI")
        return fallback_ui(project)

    # --- PARSE JSON ---
    wf = safe_json_extract(str(raw))
    if not wf:
        logger.error("❌ AI returned invalid JSON → fallback UI")
        return fallback_ui(project)

    # --- NORMALIZE INPUT KEYS ---
    for page in wf.get("pages", {}).values():
        for c in page.get("components", []):
            if "input_type" in c:
                c["inputType"] = c.pop("input_type")
            if "inputtype" in c:
                c["inputType"] = c.pop("inputtype")
            if "input-type" in c:
                c["inputType"] = c.pop("input-type")

    return wf


# -------------------------------------------------------------------
# 3) FALLBACK UI (if AI fails)
# -------------------------------------------------------------------

def fallback_ui(project: Dict[str, Any]) -> Dict[str, Any]:
    pages = {}

    for mod in project.get("modules", []):
        pid = slugify(mod["name"])

        inputs = [
            {"type": "input", "label": f, "inputType": "text"}
            for f in mod.get("fields", [])
        ]

        buttons = [
            {"type": "button", "label": a, "action": slugify(a)}
            for a in mod.get("actions", [])
        ]

        pages[pid] = {
            "title": mod["name"],
            "components": inputs + buttons
        }

    return { "pages": pages }


# -------------------------------------------------------------------
# ASYNC WRAPPER
# -------------------------------------------------------------------

async def generate_wireframe_ai(project: Dict[str, Any]):
    return generate_wireframe_ai_sync(project)
