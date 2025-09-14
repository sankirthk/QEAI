import cv2
import numpy as np
from fastapi import APIRouter, File, UploadFile, Form
from fastapi.responses import JSONResponse

from app.models.detector import Detector
from app.models.vlm import VLM
from app.models.task_manager import TaskManager

router = APIRouter()

# Initialize pipeline components
detector = Detector(weights="app/ml/best.onnx", imgsz=640)
vlm = VLM()
task_manager = TaskManager()


def _ensure_plan_from_state(detections):
    """
    If we already have a user query but still don't have a plan,
    and detections are now available, build the plan lazily.
    """
    if task_manager.query and (not task_manager.plan) and detections:
        plan = vlm.plan(detections, instruction=task_manager.query)
        task_manager.set_plan(task_manager.query, plan)


@router.post("/stream")
async def stream(
    frame: UploadFile = File(...),
    instruction: str = Form(None)  # optional, only provided once at start
):
    # Decode uploaded frame
    contents = await frame.read()
    nparr = np.frombuffer(contents, np.uint8)
    frame_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # Debug input frame (optional)
    cv2.imwrite("debug_input.jpg", frame_np)

    # Step 1: Run ONNX detection
    detections = detector.detect(frame_np)

    # Debug annotated output (optional)
    annotated = frame_np.copy()
    for det in detections:
        x1, y1, x2, y2 = det["bbox"]
        label = det["label"]
        conf = det["confidence"]
        cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(
            annotated,
            f"{label} {conf:.2f}",
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2,
        )
    cv2.imwrite("debug_output.jpg", annotated)

    # Step 2: Always remember the user's initial instruction (query),
    # even if there are no detections yet. This lets us recover later.
    if instruction:
        # Store the query so we can lazily create a plan once detections appear
        task_manager.query = instruction
        # If detections already exist right now and we don't have a plan yet, create it
        _ensure_plan_from_state(detections)

    # If we didn't get an instruction this frame but we HAVE a stored query
    # and no plan yet, try to build the plan now that we might have detections.
    if (not instruction) and task_manager.query and (not task_manager.plan) and detections:
        _ensure_plan_from_state(detections)

    # If still no detections, report and do NOT advance anything.
    if not detections:
        # longInstruction depends on whether we have an active task
        if task_manager.plan:
            long_instruction = "⚠️ No buttons detected. Please adjust the camera."
        elif task_manager.query:
            long_instruction = "⚠️ Looking for controls… please aim the camera at the panel."
        else:
            long_instruction = "⚠️ No buttons detected. Please enter a task and aim the camera."

        return JSONResponse({
            "status": "no objects",
            "overlay": [],
            "stepIndex": task_manager.current_step,
            "totalSteps": task_manager.total_steps,
            "longInstruction": long_instruction,
        })

    # Step 3: Use (possibly newly created) plan to get current step
    current_step = task_manager.get_current_instruction()
    if not current_step:
        # No active task yet (no plan created). Tell frontend to keep streaming.
        return JSONResponse({
            "status": "no active task",
            "overlay": [],
            "stepIndex": task_manager.current_step,
            "totalSteps": task_manager.total_steps,
            "longInstruction": "Enter a task to begin, then point the camera at the controls."
        })

    # Step 4: Match bbox with current active button label → overlay
    overlay = []
    for det in detections:
        if det["label"] == current_step["button_label"]:
            overlay.append({
                "bbox": det["bbox"],
                "label": det["label"],
                "confidence": det["confidence"],
                "instruction": current_step["step"],  # short instruction for overlay
            })

    # Long instruction (fallback to step if "long_step" not provided)
    long_instruction = current_step.get("long_step", f"Next: {current_step['step']}")

    # Debug
    print("[/stream] json output",
          {"overlay": overlay, "stepIndex": task_manager.current_step, "totalSteps": task_manager.total_steps})

    return JSONResponse({
        "overlay": overlay,
        "stepIndex": task_manager.current_step,
        "totalSteps": task_manager.total_steps,
        "longInstruction": long_instruction,
    })


@router.post("/step_complete")
async def step_complete():
    advanced = task_manager.complete_step()
    current_step = task_manager.get_current_instruction()

    if not advanced or current_step is None:
        # Last step completed → send a single final message
        return JSONResponse({
            "status": "done",
            "overlay": [],
            "stepIndex": task_manager.current_step,
            "totalSteps": task_manager.total_steps,
            "longInstruction": "✅ Task complete! That was the last step."
        })

    # Otherwise, return the next step
    return JSONResponse({
        "overlay": [{
            "instruction": current_step["step"],
            "label": current_step.get("button_label"),
        }],
        "stepIndex": task_manager.current_step,
        "totalSteps": task_manager.total_steps,
        "longInstruction": current_step.get("long_step", f"Next: {current_step['step']}")
    })
