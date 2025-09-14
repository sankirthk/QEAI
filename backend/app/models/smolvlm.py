import os, torch
import torch_directml
from PIL import Image
import numpy as np
from transformers import AutoProcessor, AutoModelForVision2Seq
from schemas.models import StepState
from validators import validate_next_step

VLM_ID = os.getenv("VLM_ID", "HuggingFaceTB/SmolVLM-500M-Instruct")
VLM_DEVICE = os.getenv("VLM_DEVICE", "cpu")
MAX_TOK = int(os.getenv("VLM_MAX_TOKENS", "256"))

device = torch_directml.device() if VLM_DEVICE == "dml" else VLM_DEVICE

print(f"Loading SmolVLM model {VLM_ID} on {device} ...")

processor = AutoProcessor.from_pretrained(VLM_ID, trust_remote_code=True)
model = AutoModelForVision2Seq.from_pretrained(
    VLM_ID,
    trust_remote_code=True,
    dtype=torch.float16 if str(device) == "dml" else torch.float32   # transformers >= 4.45 uses 'dtype'
).to(device)

# helper to keep the model terse + JSON only
SYS_GUARD = (
    "You are a strict JSON generator. "
    "Return ONLY a single JSON object matching: "
    "{ plan_outline?: string[], step: {index:int,title:string,action:'press'|'hold'|'toggle'|'rotate'|'select',"
    "target_button_id:string,target_label_guess?:string,bbox_xyxy?:[int,int,int,int],expected_next:string},"
    "needs_clarification?:string, ui_hint?:string }"
)

def _make_prompt(state: StepState, first_call: bool) -> str:
    btn_lines = "\n".join([f"{b.id} | {b.label} | {b.bbox_xyxy} | {b.conf:.2f}" for b in state.buttons])
    task = "Output a plan outline and the FIRST step now." if first_call else \
           f"Current step index is {state.step_index}. Output ONLY the NEXT step."
    return (
        f"{SYS_GUARD}\n"
        f"User goal: {state.user_goal}\n"
        f"Detected buttons (id | label | bbox | conf):\n{btn_lines}\n"
        f"{task}\n"
        f"Respond with STRICT JSON only."
    )

def _to_pil(img_bgr: np.ndarray | None) -> Image.Image:
    if img_bgr is None:
        # fallback blank 224x224 white (keeps the VLM happy if no image passed)
        return Image.new("RGB", (224, 224), (255, 255, 255))
    # OpenCV BGR -> PIL RGB
    return Image.fromarray(img_bgr[:, :, ::-1])


def next_step(state: StepState, first_call: bool = False, image_bgr=None) -> dict:
    prompt = _make_prompt(state, first_call)
    pil_img = _to_pil(image_bgr)

    # Build inputs for Idefics3 (image + text)
    inputs = processor(images=pil_img, text=prompt, return_tensors="pt")
    # move to device
    for k in inputs:
        inputs[k] = inputs[k].to(device)

    with torch.no_grad():
        gen_ids = model.generate(**inputs, max_new_tokens=MAX_TOK, do_sample=False, temperature=0.0)

    # decode with processor (or its tokenizer)
    try:
        text = processor.batch_decode(gen_ids, skip_special_tokens=True)[0]
    except Exception:
        text = processor.tokenizer.batch_decode(gen_ids, skip_special_tokens=True)[0]

    # Pydantic validation / light repair
    try:
        return validate_next_step(text, state.buttons)
    except Exception:
        return {
            "needs_clarification": "Assistant returned invalid JSON. Re-scan and try again.",
            "ui_hint": "Hold steady; we’ll refresh detections."
        }
