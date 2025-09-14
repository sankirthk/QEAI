import os, json
import torch
import torch_directml
from PIL import Image
import numpy as np
from transformers import AutoProcessor, AutoModelForVision2Seq


VLM_ID = os.getenv("VLM_ID", "HuggingFaceTB/SmolVLM-500M-Instruct")
VLM_DEVICE = os.getenv("VLM_DEVICE", "cpu")  # "cpu" | "cuda" | "dml"
MAX_TOK = int(os.getenv("VLM_MAX_TOKENS", "256"))
MAX_STEPS = int(os.getenv("VLM_MAX_STEPS", "8"))

device = torch_directml.device() if VLM_DEVICE == "dml" else VLM_DEVICE

processor = AutoProcessor.from_pretrained(VLM_ID, trust_remote_code=True)
model = AutoModelForVision2Seq.from_pretrained(
    VLM_ID, trust_remote_code=True,
    dtype=torch.float16 if str(device) == "dml" else torch.float32
).to(device)

SYS_CONTEXT = (
    "You are an assistant that guides the user step-by-step in operating an Instant Pot. "
    "You only know about Instant Pot front-panel buttons. Do not invent buttons or steps."
)

# Aliases to map VLM outputs to detector classnames
ALIASES = {
    "pressure cook": "pressure_cook",
    "pressure-cook": "pressure_cook",
    "pressurecook": "pressure_cook",
    "keep warm": "keep_warm",
    "keepwarm": "keep_warm",
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
    "lid_open": "lid_open",
}

def _normalize_label(lbl: str) -> str:
    l = str(lbl).strip().lower().replace("-", " ").replace("_", " ")
    l = " ".join(l.split())  # collapse spaces
    return ALIASES.get(l, lbl.strip().lower())

def _to_pil(img_bgr: np.ndarray | None) -> Image.Image:
    if img_bgr is None:
        return Image.new("RGB", (224, 224), (255, 255, 255))
    return Image.fromarray(img_bgr[:, :, ::-1])

def _make_prompt(user_goal: str, detected_buttons: list[dict]) -> str:
    allowed = [str(b.get("label", "")).strip().lower() for b in detected_buttons if b.get("label")]
    allowed = [lbl for lbl in allowed if lbl]  # filter blanks
    allowed_json = json.dumps(allowed, ensure_ascii=False)

    return (
        "You are an assistant for an Instant Pot.\n"
        "You ONLY output button-press instructions as JSON.\n\n"

        f"User goal: \"{user_goal}\"\n"
        f"Allowed button labels (choose target_label ONLY from this list): {allowed_json}\n\n"

        "Respond with JSON in exactly this format:\n"
        "{\n"
        "  \"plan_outline\": [\"short description of plan\"],\n"
        "  \"steps\": [\n"
        "    { \"index\": 0, \"title\": \"short step title\", \"instruction\": \"longer step instruction\", \"target_label\": \"one label from allowed list\" }\n"
        "  ]\n"
        "}\n\n"

        "Rules:\n"
        "- Use only labels from the allowed list.\n"
        "- Keep steps minimal and practical (1–3 steps).\n"
        "- Index must start at 0 and increase by 1.\n"
        "- If 'start' exists in allowed_labels and needed, include a final step with target_label 'start'.\n"
        "- Output ONLY valid JSON. No text outside JSON.\n\n"

        "If you cannot generate steps, return: {\"plan_outline\": [], \"steps\": []}"
    )

def _safe_json_loads(text: str) -> dict:
    try:
        return json.loads(text)
    except Exception:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end+1])
            except Exception:
                pass
    return {}

def _sanitize_plan(raw: dict, allowed_labels: set[str], user_goal: str) -> dict:
    # plan_outline
    plan_outline = raw.get("plan_outline")
    if not isinstance(plan_outline, list):
        plan_outline = []
    plan_outline = [str(x) for x in plan_outline][:MAX_STEPS]

    # steps
    raw_steps = raw.get("steps")
    if not isinstance(raw_steps, list):
        raw_steps = []

    steps = []
    seen_targets = []
    for i, s in enumerate(raw_steps):
        if not isinstance(s, dict): continue

        title = str(s.get("title") or s.get("short_instruction") or "").strip()
        instruction = str(s.get("instruction") or s.get("long_instruction") or title).strip()
        target = _normalize_label(s.get("target_label", ""))

        if not title or not target:
            continue

        # force lower + exact membership
        target = target.strip().lower()
        if target not in allowed_labels:
            continue

        steps.append({
            "index": len(steps),   # reindex 0..N-1
            "title": title,
            "instruction": instruction,
            "target_label": target
        })
        seen_targets.append(target)

    # Auto-append "rice" and/or "start" heuristics (very light-touch)
    gl = user_goal.lower()
    if not steps:
        # simple fallback: if rice in goal and available
        if "rice" in gl and "rice" in allowed_labels:
            steps.append({
                "index": 0,
                "title": "Press Rice",
                "instruction": "Press the Rice button.",
                "target_label": "rice"
            })

    # Append Start if present and not already included, and it's reasonable
    if steps and "start" in allowed_labels and steps[-1]["target_label"] != "start":
        steps.append({
            "index": len(steps),
            "title": "Press Start",
            "instruction": "Press Start to begin.",
            "target_label": "start"
        })

    return {"plan_outline": plan_outline, "steps": steps[:MAX_STEPS]}

def plan(user_goal: str, detected_buttons: list[dict], image_bgr=None) -> dict:
    prompt = _make_prompt(user_goal, detected_buttons)

    pil_img = _to_pil(image_bgr)

    # Insert <image> placeholder
    prompt_with_image = f"<image>\n{prompt}"

    # Wrap in lists so image/text count matches
    inputs = processor(images=[pil_img], text=[prompt_with_image], return_tensors="pt").to(device)

    with torch.no_grad():
        gen_ids = model.generate(
            **inputs,
            max_new_tokens=MAX_TOK,
            do_sample=False  # greedy decoding
        )

    text = processor.batch_decode(gen_ids, skip_special_tokens=True)[0]
    print("Raw model text:", text)

    raw = _safe_json_loads(text)

    allowed_labels = {
        str(b.get("label", "")).strip().lower()
        for b in detected_buttons if b.get("label")
    }
    allowed_labels = {l for l in allowed_labels if l}

    out = _sanitize_plan(raw, allowed_labels, user_goal)
    print("Sanitized plan:", out)
    return out
