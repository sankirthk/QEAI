import os
import re
import requests
import yaml
import json

# --------------------------------------------------------------------
# Config
# --------------------------------------------------------------------
with open(r"C:\Users\qc_de\Documents\PLs\edge\backend\config.yaml", "r") as file:
    config = yaml.safe_load(file)

API_KEY = config["api_key"]
BASE_URL = config["model_server_base_url"]
WORKSPACE = config["workspace_slug"]

CHAT_URL = f"{BASE_URL}/workspace/{WORKSPACE}/chat"
HEADERS = {
    "accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": "Bearer " + API_KEY,
}

MAX_STEPS = int(os.getenv("VLM_MAX_STEPS", "8"))

ALIASES = {
    "pressure cook": "pressure_cook",
    "keep warm": "keep_warm",
    "temp set": "temp_set",
    "temperature": "temp_set",
    "rice": "rice",
    "start": "start",
    "cancel": "cancel",
    "increase": "increase",
    "decrease": "decrease",
    "pressure": "pressure",
    "saute": "saute",
    "steam": "steam",
    "lid open": "lid_open",
}


# --------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------
def _normalize_label(lbl: str) -> str:
    l = str(lbl).strip().lower().replace("-", " ").replace("_", " ")
    l = " ".join(l.split())
    return ALIASES.get(l, lbl.strip().lower())


def _make_prompt(user_goal: str, detected_buttons: list[dict]) -> str:
    allowed = [str(b.get("label", "")).strip().lower() for b in detected_buttons if b.get("label")]
    allowed = [lbl for lbl in allowed if lbl]
    allowed_json = json.dumps(allowed, ensure_ascii=False)

    allowed_str = " | ".join(allowed) if allowed else "none"

    return (
        f"You are an assistant that guides a user step-by-step in operating an Instant Pot.\n"
        f"User goal: \"{user_goal}\"\n"
        f"Allowed button labels: {allowed_json}\n\n"
        "Return ONLY valid JSON in this exact format:\n"
        "{\n"
        "  \"plan_outline\": [\"short description of overall plan\"],\n"
        "  \"steps\": [\n"
        f"    {{\"index\": 0, \"title\": \"short step title\", "
        f"\"instruction\": \"longer step instruction\", "
        f"\"target_label\": \"{allowed_str}\"}}\n"
        "  ]\n"
        "}\n\n"
        "Rules:\n"
        "- For each step, target_label must be exactly one value from the allowed list above.\n"
        "- Keep steps minimal and practical (1–3 steps).\n"
        "- Index must start at 0 and increase by 1.\n"
        "- Include 'start' as the final step only if it is relevant to begin cooking and is in the allowed list.\n"
        "- Output ONLY valid JSON. No text outside JSON.\n\n"
        "JSON:"
    )


def _parse_text_response(text: str, allowed_labels: set[str]) -> list[dict]:
    """Fallback parser for Step 1 -> Button style output"""
    steps = []
    step_pattern = r"Step\s+(\d+):\s*(.+?)\s*->\s*(.+?)(?=Step\s+\d+:|$)"
    matches = re.findall(step_pattern, text, re.IGNORECASE | re.DOTALL)

    for i, (_, description, button_name) in enumerate(matches):
        target = _normalize_label(button_name.strip())
        if target in allowed_labels:
            steps.append(
                {
                    "index": i,
                    "title": description.strip(),
                    "instruction": f"Press the {button_name.strip()} button.",
                    "target_label": target,
                }
            )
    return steps


def _sanitize_plan(text: str, allowed_labels: set[str], user_goal: str) -> dict:
    """Parse model output -> structured plan"""
    steps = []

    print("\n========== Raw model output ==========")
    print(text[:1000])  # log first 1000 chars
    print("======================================\n")

    # --- Try strict JSON parse first ---
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict) and "steps" in parsed:
            for i, step in enumerate(parsed["steps"]):
                target = _normalize_label(step.get("target_label", "").strip())
                if target in allowed_labels:
                    steps.append({
                        "index": step.get("index", i),
                        "title": step.get("title", f"Step {i+1}"),
                        "instruction": step.get("instruction", step.get("title", f"Step {i+1}")),
                        "target_label": target,
                    })
    except Exception as e:
        print("JSON parse failed, falling back to regex. Error:", e)
        steps = _parse_text_response(text, allowed_labels)

    # --- Heuristic fallback ---
    if not steps:
        gl = user_goal.lower()
        if "rice" in gl and "rice" in allowed_labels:
            steps.append({
                "index": 0,
                "title": "Cook Rice",
                "instruction": "Press the Rice button.",
                "target_label": "rice",
            })
        elif "pressure cook" in gl and "pressure_cook" in allowed_labels:
            steps.append({
                "index": 0,
                "title": "Pressure Cook",
                "instruction": "Press the Pressure Cook button.",
                "target_label": "pressure_cook",
            })
        elif "saute" in gl and "saute" in allowed_labels:
            steps.append({
                "index": 0,
                "title": "Sauté",
                "instruction": "Press the Sauté button.",
                "target_label": "saute",
            })

    # --- Append Start if relevant ---
    if steps and "start" in allowed_labels and steps[-1]["target_label"] != "start":
        steps.append({
            "index": len(steps),
            "title": "Start Cooking",
            "instruction": "Press Start to begin cooking.",
            "target_label": "start",
        })

    steps = steps[:MAX_STEPS]

    print("\n========== Sanitized plan ==========")
    print(json.dumps(steps, indent=2))
    print("===================================\n")

    return {"plan_outline": [s["title"] for s in steps], "steps": steps}


# --------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------
def plan(user_goal: str, detected_buttons: list[dict], image_bgr=None) -> dict:
    """
    Generate a cooking plan using LLaMA via AnythingLLM.
    (image_bgr is ignored, kept for API compatibility)
    """
    prompt = _make_prompt(user_goal, detected_buttons)

    data = {
        "message": prompt,
        "mode": "chat",
        "sessionId": "instantpot-session",
        "attachments": [],
    }

    try:
        resp = requests.post(CHAT_URL, headers=HEADERS, json=data, timeout=60)
        resp.raise_for_status()
        text = resp.json().get("textResponse", "")
    except Exception as e:
        print("Error calling AnythingLLM:", e)
        return {"plan_outline": [], "steps": []}

    allowed_labels = {_normalize_label(b["label"]) for b in detected_buttons if b.get("label")}
    return _sanitize_plan(text, allowed_labels, user_goal)
