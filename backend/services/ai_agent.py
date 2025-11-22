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
• Convert module fields → INPUT components.
• Convert module actions → BUTTON components.
• Group related actions into logical pages (login, otp_verification, register, password_recovery).
• Choose correct inputType based on label (email, password, tel, date, number, file, select, textarea).
• Output JSON ONLY.

IMPORTANT RULES:
• Output ONLY valid JSON — no text, no markdown.
• Do NOT include layout, navigation, app_name, colors.
• Pages must be nested under module slug.
• Use lowercase_with_underscores for all slugs.

REQUIRED JSON SCHEMA EXAMPLE:

{{
  "pages": {{
    "<module_slug>": {{
      "<page_slug>": {{
        "title": "<Page Title>",
        "description": "",
        "components": [
          {{
            "type": "input",
            "label": "Email",
            "name": "email",
            "inputType": "email",
            "required": true
          }},
          {{
            "type": "button",
            "label": "Login",
            "action": "login"
          }}
        ]
      }}
    }}
  }}
}}

GUIDELINES:
• Login flow should have: login, otp_verification, register, forgot_password.
• Customer modules should have: profile, address_list, order_history, wallet, favorites, etc.
• Make pages meaningful, not a single dump of all fields.
• Use logical grouping: inputs first → buttons last.
• Use correct input types.

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

    # --------------------------------------------------
    # DEBUG — Print FINAL prompt sent to LLaMA
    # --------------------------------------------------
    print("\n================ LLaMA PROMPT SENT =================\n")
    print(prompt)
    print("\n====================================================\n")

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }

    # --- CALL LLaMA ---
    try:
        resp = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=120)
        body = resp.json()

        # LLaMA returns either:
        # { "response": "text" }
        # { "output": "text" }
        raw = body.get("response") or body.get("output") or ""

        # If streaming chunks came as list
        if isinstance(raw, list):
            raw = "".join(
                chunk.get("response", "") 
                for chunk in raw 
                if isinstance(chunk, dict)
            )

    except Exception as e:
        logger.error("❌ AI request failed, using fallback UI")
        print("AI ERROR:", e)
        return fallback_ui(project)

    # --------------------------------------------------
    # DEBUG — Print EXACT RAW AI TEXT
    # --------------------------------------------------
    print("\n================ RAW LLaMA OUTPUT =================\n")
    print(raw)
    print("\n===================================================\n")

    # --- PARSE JSON ---
    wf = safe_json_extract(str(raw))
    if not wf:
        logger.error("❌ AI returned invalid JSON → fallback UI")
        return fallback_ui(project)

    # --------------------------------------------------
    # NORMALIZE INPUT TYPES
    # --------------------------------------------------
    for module_slug, module_pages in wf.get("pages", {}).items():
        for page_slug, page in module_pages.items():
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
        module_slug = slugify(mod["name"])

        inputs = [
            {"type": "input", "label": f, "inputType": "text", "name": slugify(f)}
            for f in mod.get("fields", [])
        ]

        buttons = [
            {"type": "button", "label": a, "action": slugify(a)}
            for a in mod.get("actions", [])
        ]

        pages[module_slug] = {
            "main": {
                "title": mod["name"],
                "description": "",
                "components": inputs + buttons
            }
        }

    return {"pages": pages}

# -------------------------------------------------------------------
# ASYNC WRAPPER
# -------------------------------------------------------------------

async def generate_wireframe_ai(project: Dict[str, Any]):
    return generate_wireframe_ai_sync(project)
