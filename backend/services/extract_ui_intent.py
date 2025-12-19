from bs4 import BeautifulSoup

def extract_ui_intent_from_html(html: str):
    soup = BeautifulSoup(html, "lxml")
    sections = soup.find_all("section")

    pages = []

    for section in sections:
        page_id = section.get("id")
        title = section.find("h1")
        page_name = title.get_text(strip=True) if title else ""

        inputs = []
        for field in section.find_all(["input", "textarea", "select"]):
            inputs.append({
                "name": field.get("id") or field.get("name"),
                "type": field.name,
                "required": field.has_attr("required")
            })

        pages.append({
            "page_id": page_id,
            "page_name": page_name,
            "inputs": inputs
        })

    return {
        "source": "wireframe_html",
        "pages": pages
    }
