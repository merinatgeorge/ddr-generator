import fitz
import json
import os
from groq import Groq
from dotenv import load_dotenv
from prompts import DDR_SYSTEM_PROMPT, DDR_USER_PROMPT

load_dotenv()

def extract_text_from_pdf(pdf_file) -> str:
    pdf_file.seek(0)
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def extract_images_from_pdf(pdf_file) -> list:
    pdf_file.seek(0)
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    images = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        image_list = page.get_images(full=True)
        for img_index, img in enumerate(image_list):
            xref = img[0]
            try:
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                if image_ext.lower() in ["jpeg", "jpg", "png"]:
                    images.append({
                        "bytes": image_bytes,
                        "ext": image_ext,
                        "page": page_num + 1,
                        "index": img_index
                    })
            except Exception:
                continue
    return images

def generate_ddr_data(inspection_text: str, thermal_text: str) -> dict:
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    user_message = DDR_USER_PROMPT.format(
        inspection_text=inspection_text[:12000],
        thermal_text=thermal_text[:6000]
    )

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": DDR_SYSTEM_PROMPT},
            {"role": "user",   "content": user_message}
        ],
        temperature=0.3,
        max_tokens=4000,
    )

    raw = response.choices[0].message.content

    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0]
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0]

    raw = raw.strip()
    parsed = json.loads(raw)

    if isinstance(parsed, list):
        parsed = {"area_observations": parsed}

    result = {
        "property_summary": parsed.get("property_summary", {
            "overview": "Not Available", "areas": []
        }),
        "area_observations": parsed.get("area_observations", []),
        "root_causes": parsed.get("root_causes", []),
        "severity": parsed.get("severity", []),
        "recommended_actions": parsed.get("recommended_actions", {
            "immediate": [], "short_term": [], "long_term": []
        }),
        "additional_notes": parsed.get("additional_notes", []),
        "missing_info": parsed.get("missing_info", []),
    }

    fixed_observations = []
    for obs in result["area_observations"]:
        if isinstance(obs, str):
            fixed_observations.append({
                "area": obs,
                "negative_side": "Not Available",
                "positive_side": "Not Available",
                "thermal_finding": "Not Available"
            })
        elif isinstance(obs, dict):
            fixed_observations.append(obs)
    result["area_observations"] = fixed_observations

    fixed_severity = []
    for sev in result["severity"]:
        if isinstance(sev, str):
            fixed_severity.append({
                "area": sev,
                "level": "Moderate",
                "reasoning": "Not Available",
                "action": "Not Available"
            })
        elif isinstance(sev, dict):
            fixed_severity.append(sev)
    result["severity"] = fixed_severity

    return result