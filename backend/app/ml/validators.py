# app/validators.py
import json, re
from typing import Any, Dict, List
from pydantic import BaseModel
from models import Button, Step


class NextStepModel(BaseModel):
    plan_outline: List[str] | None = None
    step: Step
    needs_clarification: str | None = None
    ui_hint: str | None = None


def _extract_json(text: str) -> str:
    """Grab the first top-level JSON object from possibly chatty text."""
    start = text.find("{")
    end = len(text) - 1
    if start == -1:
        raise ValueError("No JSON object found")
    bal = 0
    for i, ch in enumerate(text[start:], start):
        if ch == "{":
            bal += 1
        elif ch == "}":
            bal -= 1
            if bal == 0:
                end = i
                break
    return text[start:end+1]


def _light_repair(js: str) -> str:
    """Minimal, deterministic repairs (edge-safe)."""
    js = re.sub(r"'", '"', js)
    js = re.sub(r",\s*([}\]])", r"\1", js)
    return js


def validate_next_step(raw_text: str, current_buttons: List[Button]) -> dict:
    # 1) parse JSON
    try:
        payload = json.loads(raw_text)
    except Exception:
        try:
            js = _extract_json(raw_text)
            payload = json.loads(js)
        except Exception:
            js = _light_repair(_extract_json(raw_text))
            payload = json.loads(js)

    # 2) top-level shape
    data = NextStepModel(**payload).model_dump()

    # 3) check if target_label exists in current buttons
    labels = {b.label.lower() for b in current_buttons}
    if data["step"]["target_label"].lower() not in labels:
        return {
            "needs_clarification": f"Target button {data['step']['target_label']} not found in current view.",
            "ui_hint": "Recenter camera so the missing button is visible."
        }

    return data
