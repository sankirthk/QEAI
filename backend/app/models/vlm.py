# import os
# import re
# import json
# from openai import OpenAI

# # --------------------------------------------------------------------
# # Config
# # --------------------------------------------------------------------
# OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/v1")
# OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "deepseek-r1:7b")

# MAX_STEPS = int(os.getenv("VLM_MAX_STEPS", "8"))

# ALIASES = {
#     "pressure cook": "pressure_cook",
#     "keep warm": "keep_warm",
#     "temp set": "temp_set",
#     "temperature": "temp_set",
#     "rice": "rice",
#     "start": "start",
#     "cancel": "cancel",
#     "increase": "increase",
#     "decrease": "decrease",
#     "pressure": "pressure",
#     "saute": "saute",
#     "steam": "steam",
#     "lid open": "lid_open",
# }

# # --------------------------------------------------------------------
# # OpenAI-compatible client for Ollama
# # --------------------------------------------------------------------
# client = OpenAI(base_url=OLLAMA_URL, api_key="ollama")  # dummy key, Ollama ignores it

# # --------------------------------------------------------------------
# # Helpers
# # --------------------------------------------------------------------
# def _normalize_label(lbl: str) -> str:
#     l = str(lbl).strip().lower().replace("-", " ").replace("_", " ")
#     l = " ".join(l.split())
#     return ALIASES.get(l, lbl.strip().lower())


# def _make_prompt(user_goal: str, detected_buttons: list[dict]) -> str:
#     allowed = [str(b.get("label", "")).strip().lower() for b in detected_buttons if b.get("label")]
#     allowed = [lbl for lbl in allowed if lbl]
#     # allowed_str = " | ".join(allowed) if allowed else "none"

#     return f"""
# You are a JSON generator.
# Always return valid JSON only.

# Schema:
# {{
#   "steps": [
#     {{
#       "index": number,
#       "title": string,
#       "instruction": string,
#       "target_label": one of ["rice","pressure_cook","keep_warm","start","cancel","increase","decrease","temp_set"]
#     }}
#   ]
# }}

# Do not include any text outside JSON. Do not explain. Do not add prose.

# ### Example 1
# User request: Cook rice
# Output:
# {{
#   "steps": [
#     {{
#       "index": 0,
#       "title": "select rice mode",
#       "instruction": "Press the rice button",
#       "target_label": "rice"
#     }},
#     {{
#       "index": 1,
#       "title": "start cooking",
#       "instruction": "Press start to begin cooking",
#       "target_label": "start"
#     }}
#   ]
# }}

# ### Example 2
# User request: Keep food warm
# Output:
# {{
#   "steps": [
#     {{
#       "index": 0,
#       "title": "activate keep warm",
#       "instruction": "Press the keep warm button",
#       "target_label": "keep_warm"
#     }}
#   ]
# }}

# ### Now your turn
# User request: {user_goal}
# Output:
# """

# def _sanitize_plan(text: str, allowed_labels: set[str], user_goal: str) -> dict:
#     """Parse model output -> structured plan"""
#     steps = []

#     print("\n========== Raw model output ==========")
#     print(text[:1000])
#     print("======================================\n")

#     # Try JSON parse first
#     try:
#         parsed = json.loads(text)
#         if isinstance(parsed, dict) and "steps" in parsed:
#             for i, step in enumerate(parsed["steps"]):
#                 target = _normalize_label(step.get("target_label", "").strip())
#                 if target in allowed_labels:
#                     steps.append({
#                         "index": step.get("index", i),
#                         "title": step.get("title", f"Step {i+1}"),
#                         "instruction": step.get("instruction", step.get("title", f"Step {i+1}")),
#                         "target_label": target,
#                     })
#     except Exception as e:
#         print("JSON parse failed, fallback error:", e)

#     # Heuristic fallback
#     if not steps:
#         gl = user_goal.lower()
#         if "rice" in gl and "rice" in allowed_labels:
#             steps.append({"index": 0, "title": "Cook Rice", "instruction": "Press the Rice button.", "target_label": "rice"})
#         elif "pressure cook" in gl and "pressure_cook" in allowed_labels:
#             steps.append({"index": 0, "title": "Pressure Cook", "instruction": "Press the Pressure Cook button.", "target_label": "pressure_cook"})
#         elif "saute" in gl and "saute" in allowed_labels:
#             steps.append({"index": 0, "title": "Sauté", "instruction": "Press the Sauté button.", "target_label": "saute"})

#     # Append Start if relevant
#     if steps and "start" in allowed_labels and steps[-1]["targe t_label"] != "start":
#         steps.append({"index": len(steps), "title": "Start Cooking", "instruction": "Press Start to begin cooking.", "target_label": "start"})

#     steps = steps[:MAX_STEPS]

#     print("\n========== Sanitized plan ==========")
#     print(json.dumps(steps, indent=2))
#     print("===================================\n")

#     return {"plan_outline": [s["title"] for s in steps], "steps": steps}

# # --------------------------------------------------------------------
# # Public API
# # --------------------------------------------------------------------
# def plan(user_goal: str, detected_buttons: list[dict], image_bgr=None) -> dict:
#     """
#     Generate a cooking plan using DeepSeek via Ollama (OpenAI chat completions).
#     """
#     prompt = _make_prompt(user_goal, detected_buttons)

#     try:
#         resp = client.chat.completions.create(
#             model=OLLAMA_MODEL,
#             messages=[
#                 {"role": "system", "content": "You are an assistant that outputs only JSON."},
#                 {"role": "user", "content": prompt}
#             ],
#             temperature=0,
#         )
#         text = resp.choices[0].message.content
#     except Exception as e:
#         print("Error calling Ollama via OpenAI client:", e)
#         return {"plan_outline": [], "steps": []}

#     allowed_labels = {_normalize_label(b["label"]) for b in detected_buttons if b.get("label")}
#     return _sanitize_plan(text, allowed_labels, user_goal)

import os
from typing import List, Literal
from pydantic import BaseModel
from ollama import chat

# --------------------------------------------------------------------
# Config
# --------------------------------------------------------------------
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "deepseek-r1:7b")
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
# Schema
# --------------------------------------------------------------------
class Step(BaseModel):
    index: int
    title: str
    instruction: str
    target_label: Literal[
        "rice", "pressure_cook", "keep_warm", "start",
        "cancel", "increase", "decrease", "temp_set",
        "saute", "steam", "lid_open", "pressure"
    ]

class StepList(BaseModel):
    steps: List[Step]

# --------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------
def _normalize_label(lbl: str) -> str:
    l = str(lbl).strip().lower().replace("-", " ").replace("_", " ")
    l = " ".join(l.split())
    return ALIASES.get(l, lbl.strip().lower())

# --------------------------------------------------------------------
# Main planning function
# --------------------------------------------------------------------
def plan(user_goal: str, detected_buttons: list[dict], image_bgr=None) -> dict:
    """
    Generate a cooking plan using DeepSeek via Ollama structured outputs.
    """
    try:
        btns = [b["label"] for b in detected_buttons if b.get("label")]
        btn_str = ", ".join(btns) if btns else "rice, pressure_cook, keep_warm, start, cancel"

        response = chat(
            model=OLLAMA_MODEL,
            messages=[
                {
                    "role": "user", 
                    "content": (
                        f"Create Instant Pot steps for: {user_goal}\n"
                        "MUST specify exact ingredients and amounts in every instruction.\n\n"
                        
                        "MODES: rice, pressure_cook, saute, steam, keep_warm\n"
                        "MODIFIERS: pressure, increase, decrease\n" 
                        "ACTIONS: start, cancel, lid_open\n\n"
                        
                        "ORDER: 1) Add ingredients - like rice, vegetables, etc, (lid_open) 2) Select mode 3) Adjust settings 4) Press start\n\n"
                        
                        "Example - Chicken and rice:\n"
                        "{{\"steps\": [\n"
                        "  {{\"index\": 0, \"title\": \"add chicken\", \"instruction\": \"Add 2 lbs chicken breast + 2 cups chicken broth\", \"target_label\": \"lid_open\"}},\n"
                        "  {{\"index\": 1, \"title\": \"pressure cook\", \"instruction\": \"Close lid, press pressure cook button\", \"target_label\": \"pressure_cook\"}},\n"
                        "  {{\"index\": 2, \"title\": \"set time\", \"instruction\": \"Press increase to 15 minutes\", \"target_label\": \"increase\"}},\n"
                        "  {{\"index\": 3, \"title\": \"start cooking\", \"instruction\": \"Press start\", \"target_label\": \"start\"}},\n"
                        "  {{\"index\": 4, \"title\": \"add rice\", \"instruction\": \"Quick release, add 1 cup rice + 1 cup water\", \"target_label\": \"lid_open\"}},\n"
                        "  {{\"index\": 5, \"title\": \"cook again\", \"instruction\": \"Close lid, press rice button\", \"target_label\": \"rice\"}},\n"
                        "  {{\"index\": 6, \"title\": \"start\", \"instruction\": \"Press start\", \"target_label\": \"start\"}}\n"
                        "]}}\n\n"
                        
                        "JSON only:"
                    ),
                }
            ],
            format=StepList.model_json_schema(),
            options={"temperature": 0.1},
        )
        parsed = StepList.model_validate_json(response.message.content)

        # Filter against detected button labels if provided
        allowed_labels = {_normalize_label(b["label"]) for b in detected_buttons if b.get("label")}
        filtered_steps = [
            step for step in parsed.steps if step.target_label in allowed_labels or not allowed_labels
        ]

        # Truncate to max steps
        filtered_steps = filtered_steps[:MAX_STEPS]
        print(f"####################### {filtered_steps} ######################")
        return {
            "plan_outline": [s.title for s in filtered_steps],
            "steps": [s.dict() for s in filtered_steps],
        }

    except Exception as e:
        print("Error calling Ollama with structured output:", e)
        return {"plan_outline": [], "steps": []}