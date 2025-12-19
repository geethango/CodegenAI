# =============================================================================
# services/api_prompt.py
# =============================================================================

import json
from typing import Dict, Any


API_PROMPT_TEMPLATE = """
You are a senior backend architect.

Your task is to generate REST APIs using FastAPI
based STRICTLY on the provided UI intent JSON.

========================
INPUT
UI intent JSON describes:
• User-visible pages
• User actions
• Input fields

========================
OUTPUT REQUIREMENTS (STRICT)

• Output ONLY valid JSON
• NO markdown
• NO explanations
• NO comments
• NO trailing text

========================
API DESIGN RULES

• One API per page
• Use REST conventions
• Predict HTTP method from page purpose
• Use JSON request/response bodies
• API paths must be deterministic
• Use snake_case for fields
• Use kebab-case for URL paths

========================
HTTP METHOD INFERENCE

Use the following mapping:

• login, register, send, verify, reset, add, create → POST
• edit, update → PUT
• delete, remove → DELETE
• view, list, get → GET
• logout → POST

========================
AUTH RULES

• auth-* modules → auth_required = false
• all other modules → auth_required = true

========================
REQUEST SCHEMA RULES

• Derive request fields ONLY from inputs[]
• Use input.name as field name
• input.type mapping:
  - input → string
  - textarea → string
  - select → string
• required=false → optional field

========================
RESPONSE SCHEMA (STANDARD)

Every API must return:

{
  "success": boolean,
  "message": string,
  "data": object | null
}

========================
OUTPUT JSON STRUCTURE (MANDATORY)

{
  "api_version": "v1",
  "apis": [
    {
      "name": string,
      "method": "GET | POST | PUT | DELETE",
      "path": string,
      "auth_required": boolean,
      "request_schema": { },
      "response_schema": { },
      "description": string
    }
  ]
}

========================
IMPORTANT CONSTRAINTS

• Generate APIs ONLY for pages in ui_intent.pages[]
• DO NOT invent pages, fields, or modules
• DO NOT rename input fields
• DO NOT merge multiple pages into one API
• DO NOT skip any page

========================
UI INTENT JSON:
{ui_intent_json}
"""


def build_api_prompt(ui_intent: Dict[str, Any]) -> str:
    """
    Build Gemini prompt for API generation from UI intent
    """

    return API_PROMPT_TEMPLATE.format(
        ui_intent_json=json.dumps(ui_intent, indent=2)
    )
