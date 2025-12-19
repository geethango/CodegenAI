# =============================================================================
# services/wireframe_prompt.py
# =============================================================================

import json
from typing import Dict, Any

PROMPT_TEMPLATE = """
You are a senior UI/UX architect generating a STATIC HTML wireframe
for a real consumer web application.

========================
GOAL

Generate ONE static HTML5 document that visually represents
user-facing application pages as real-world app-like low-fidelity wireframes,
not documentation or text blocks.

This is a SINGLE-PAGE document using anchor navigation.

========================
CRITICAL VISUAL REQUIREMENT

Each page MUST visually appear as a standalone CARD.

========================
OUTPUT RULES (STRICT)

• Output ONLY raw HTML
• Start with <!DOCTYPE html>
• End with </html>
• NO markdown
• NO explanations
• NO comments

========================
TECHNICAL RULES

• HTML5 only
• Inline CSS only
• NO JavaScript
• Max width: 700px
• Font: Arial

========================
PAGE STRUCTURE RULES

• ONE <section> = ONE page
• EACH section MUST have a unique id
• Section id format: module-name__page-name
• Lowercase, hyphen-separated

========================
NAVIGATION RULES

• Anchor navigation only
• <a href="#section-id">
• Every section must have at least one link pointing to it

========================
FINAL

Return ONLY pure static HTML.

PROJECT JSON:
{project_json}
"""


def build_wireframe_prompt(project: Dict[str, Any]) -> str:
    """
    Build Gemini prompt for wireframe generation
    """

    clean_project = {
        "title": project.get("title"),
        "modules": project.get("modules", [])
    }

    return PROMPT_TEMPLATE.format(
        project_json=json.dumps(clean_project, indent=2)
    )
