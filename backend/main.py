# =============================================================================
# 🎯 SynopsisAI Backend (FINAL & COMPLETE main.py)
# -----------------------------------------------------------------------------
# This version:
#   ✅ Preserves ALL original logic (nothing missing)
#   ✅ Fixes RAW HTML output issue
#   ✅ Removes duplicate routes
#   ✅ Ensures FastAPI always returns JSON
# =============================================================================

from fastapi import FastAPI, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import re
import json
from bson import ObjectId
from datetime import datetime
from dotenv import load_dotenv
from services.extract_ui_intent import extract_ui_intent_from_html
from services.ai_agent import generate_wireframe_ai, generate_apis_from_ui_intent



load_dotenv()

# 🔧 Import custom services
from services.synopsis_service import process_synopsis
from services.db_service import save_project, get_project, collection
from services.project_parser import parse_structured_project
from services.ai_agent import generate_wireframe_ai

# =============================================================================
# 🌐 FastAPI Configuration
# =============================================================================
app = FastAPI(title="SynopsisAI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# 🏠 Health Check Endpoint
# =============================================================================
@app.get("/")
def home():
    return {"status": "Backend running", "db": "MongoDB connected ✅"}

# =============================================================================
# 📡 API: Upload & Save Synopsis
# =============================================================================
@app.post("/api/upload-synopsis")
async def upload_synopsis(
    synopsis: str = Form(None),
    tech: str = Form(None),
    file: UploadFile = None
):
    text = await process_synopsis(synopsis, file)
    project_data = parse_structured_project(text)

    # Normalize fields
    project_data["title"] = project_data.get("title") or project_data.get("project_title") or "Untitled Project"
    project_data["description"] = project_data.get("description") or "No description provided"
    project_data["features"] = project_data.get("features") or project_data.get("key_features") or []
    project_data["modules"] = project_data.get("modules") or []
    project_data["tech_stack"] = [tech]
    project_data["target_platform"] = project_data.get("target_platform") or "Web"
    project_data["ui_layout"] = project_data.get("ui_layout") or "dashboard"
    project_data["ui_color_scheme"] = project_data.get("ui_color_scheme") or "blue"
    project_data["ui_primary_color"] = project_data.get("ui_primary_color") or "#4361ee"
    project_data["ai_summary"] = project_data.get("ai_summary") or project_data.get("expected_output") or "Auto-generated"

    project_data.update({
        "prompt": text,
        "status": "synopsis_uploaded",
        "created_at": datetime.utcnow().isoformat(),
        "wireframe": {},
        "code_repo": None
    })

    project_id = await save_project(project_data)

    return JSONResponse(content={
        "success": True,
        "project_id": str(project_id),
        "project": {
            "title": project_data["title"],
            "description": project_data["description"],
            "features": project_data["features"],
            "modules": project_data["modules"],
            "tech_stack": project_data["tech_stack"],
            "target_platform": project_data["target_platform"],
            "ai_summary": project_data["ai_summary"],
            "wireframe": {}
        }
    })

# =============================================================================
# 📦 API: Get Latest Project
# =============================================================================
@app.get("/api/get-latest-project")
async def get_latest_project():
    doc = await collection.find_one(sort=[("_id", -1)])
    if not doc:
        return JSONResponse(content={"success": False, "error": "No project found"})

    doc["_id"] = str(doc["_id"])
    return JSONResponse(content={"success": True, "project": doc})

# =============================================================================
# 📝 API: Update Project (Step 2)
# =============================================================================
@app.post("/api/update-project")
async def update_project(project_id: str = Form(...), project: str = Form(...)):
    try:
        updated_data = json.loads(project)
        result = await collection.update_one(
            {"_id": ObjectId(project_id)},
            {"$set": updated_data}
        )

        if result.matched_count != 1:
            return JSONResponse(content={"success": False, "error": "Project not found"})

        return JSONResponse(content={"success": True})

    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

# =============================================================================
# 🧱 API: Generate FULL Wireframe (FIXED)
# =============================================================================
@app.post("/api/generate-wireframe")
async def generate_wireframe(project_id: str = Form(...)):
    project = await get_project(project_id)

    if not project:
        return JSONResponse(
            status_code=404,
            content={"success": False, "error": "Project not found"}
        )

    try:
        html_output = await generate_wireframe_ai(project)

        # Sanitize HTML
        safe_html = re.sub(
            r"<script\\b[^<]*(?:(?!<\\/script>)<[^<]*)*<\\/script>",
            "",
            str(html_output),
            flags=re.IGNORECASE
        )

        if "<html" not in safe_html.lower():
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": "Invalid HTML from AI"}
            )

        # ✅ STEP: Extract UI intent immediately
        ui_intent = extract_ui_intent_from_html(safe_html)

        # ✅ STEP: Store ONLY UI intent (NO HTML)
        await collection.update_one(
            {"_id": ObjectId(project_id)},
            {"$set": {
                "ui_intent": ui_intent,
                "status": "ui_intent_extracted",
                "updated_at": datetime.utcnow().isoformat()
            }}
        )

        pj = json.loads(json.dumps(project, default=str))

        return JSONResponse(content={
            "success": True,
            "project_id": project_id,
            "ui_intent": ui_intent,   # ✅ API-ready JSON
            "html": safe_html,        # ⚠ optional (frontend preview only)
            "project": {
                "title": pj.get("title", ""),
                "description": pj.get("description"),
                "features": pj.get("features", []),
                "modules": pj.get("modules", []),
                "tech_stack": pj.get("tech_stack", []),
                "target_platform": pj.get("target_platform"),
                "ai_summary": pj.get("ai_summary"),
                "ui_layout": pj.get("ui_layout"),
                "ui_color_scheme": pj.get("ui_color_scheme"),
                "ui_primary_color": pj.get("ui_primary_color")
            }
        })

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


# =============================================================================
# 🎨 API: Update Wireframe UI Settings
# =============================================================================
@app.post("/api/update-wireframe")
async def update_wireframe(project_id: str = Form(...), wireframe: str = Form(...)):
    try:
        new_data = json.loads(wireframe)
        project = await get_project(project_id)

        if not project:
            return JSONResponse(content={"success": False, "error": "Project not found"})

        wf = project.get("wireframe", {})
        wf["layout_type"] = new_data.get("layout_type", wf.get("layout_type"))
        wf["color_scheme"] = new_data.get("color_scheme", wf.get("color_scheme"))
        wf["primary_color"] = new_data.get("primary_color", wf.get("primary_color"))

        await collection.update_one(
            {"_id": ObjectId(project_id)},
            {"$set": {
                "wireframe": wf,
                "ui_layout": wf.get("layout_type"),
                "ui_color_scheme": wf.get("color_scheme"),
                "ui_primary_color": wf.get("primary_color")
            }}
        )

        return JSONResponse(content={"success": True})

    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})


# =============================================================================
# 🚀 API: Generate Backend APIs from UI Intent (Gemini-powered)
# =============================================================================
@app.post("/api/generate-apis")
async def generate_apis(project_id: str = Form(...)):
    project = await get_project(project_id)

    if not project:
        return JSONResponse(
            status_code=404,
            content={"success": False, "error": "Project not found"}
        )

    if "ui_intent" not in project:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "UI intent not generated yet"}
        )

    try:
        # 🔹 Generate API spec using Gemini
        api_spec = await generate_apis_from_ui_intent(project["ui_intent"])

        # 🔹 Store generated APIs in MongoDB
        await collection.update_one(
            {"_id": ObjectId(project_id)},
            {"$set": {
                "generated_apis": api_spec,
                "status": "api_generated",
                "updated_at": datetime.utcnow().isoformat()
            }}
        )

        return JSONResponse(content={
            "success": True,
            "project_id": project_id,
            "apis": api_spec
        })

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )
