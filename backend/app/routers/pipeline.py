from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
import cv2, numpy as np, json
from collections import deque

from app.models.detector import Detector
from app.models.task_manager import TaskManager
from app.models.vlm import plan

router = APIRouter()

# Detector now returns boxes in ORIGINAL frame coordinates
detector = Detector(weights="app/ml/best.pt", imgsz=640)
task_manager = TaskManager()
_detection_buffer = deque(maxlen=3)


def _labels_for_vlm(detections):
    return [{"label": str(d.get("label", "")).strip().lower()} for d in detections if d.get("label")]


def _ensure_plan_from_state(detections):
    if not task_manager.query:
        return
    vlm_buttons = _labels_for_vlm(detections)
    vlm_response = plan(task_manager.query, vlm_buttons)

    steps_out = []
    for i, step in enumerate(vlm_response.get("steps", [])):
        steps_out.append({
            "index": i,
            "title": step.get("title", f"Step {i+1}"),
            "instruction": step.get("instruction", f"Step {i+1}"),
            "target_label": str(step.get("target_label", "")).strip().lower(),
        })

    if steps_out:
        task_manager.set_plan(task_manager.query, steps_out)


@router.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            try:
                message = await websocket.receive()
            except (WebSocketDisconnect, RuntimeError):
                break

            # --- TEXT message (instruction) ---
            if "text" in message:
                try:
                    data = json.loads(message["text"])
                except Exception:
                    continue
                if data.get("type") == "instruction":
                    # RESET state on new task
                    task_manager.reset()
                    task_manager.query = data.get("task", "")
                    await websocket.send_text(json.dumps({"status": "instruction_received"}))

            # --- BINARY message (frame) ---
            elif "bytes" in message:
                frame_bytes = message["bytes"]
                nparr = np.frombuffer(frame_bytes, np.uint8)
                frame_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                detections = detector.detect(frame_np)

                # Require some minimum detections before planning
                _detection_buffer.append(len(detections) >= 5)

                if task_manager.query and not task_manager.plan and all(_detection_buffer) and len(_detection_buffer) == 3:
                    _ensure_plan_from_state(detections)

                if not detections:
                    li = " No buttons detected. Please adjust the camera." if task_manager.query else " No task set."
                    await websocket.send_text(json.dumps({
                        "status": "no objects",
                        "overlay": [],
                        "stepIndex": task_manager.current_step,
                        "totalSteps": task_manager.total_steps,
                        "longInstruction": li,
                    }))
                    continue

                if task_manager.query and not task_manager.plan:
                    await websocket.send_text(json.dumps({
                        "status": "waiting",
                        "overlay": [],
                        "stepIndex": 0,
                        "totalSteps": 0,
                        "longInstruction": "Align camera to show enough buttons clearly.",
                    }))
                    continue

                current_step = task_manager.get_current_instruction()
                if not current_step:
                    await websocket.send_text(json.dumps({
                        "status": "no active task",
                        "overlay": [],
                        "stepIndex": 0,
                        "totalSteps": 0,
                        "longInstruction": "Enter a task to begin.",
                    }))
                    continue

                # match current step target to detections
                target = current_step["target_label"]
                matches = [d for d in detections if str(d["label"]).strip().lower() == target]
                best_det = max(matches, key=lambda d: d["confidence"], default=None)

                overlay = []
                if best_det:
                    overlay.append({
                        "bbox": best_det["bbox"],  # already in original frame coords
                        "label": best_det["label"],
                        "confidence": best_det["confidence"],
                        "instruction": current_step["title"],
                    })

                await websocket.send_text(json.dumps({
                    "status": "ok",
                    "overlay": overlay,
                    "stepIndex": task_manager.current_step,
                    "totalSteps": task_manager.total_steps,
                    "longInstruction": current_step.get("instruction", f"Next: {current_step['title']}")
                }))

    finally:
        try:
            if not websocket.client_state.DISCONNECTED:
                await websocket.close()
        except Exception:
            pass


@router.post("/step_complete")
async def step_complete():
    if not task_manager.query or not task_manager.plan or task_manager.current_step >= task_manager.total_steps:
        task_manager.reset()
        return JSONResponse({
            "status": "done",
            "overlay": [],
            "stepIndex": 0,
            "totalSteps": 0,
            "longInstruction": " Task complete!"
        })

    advanced = task_manager.complete_step()
    current_step = task_manager.get_current_instruction()

    if not advanced or not current_step:
        task_manager.reset()
        return JSONResponse({
            "status": "done",
            "overlay": [],
            "stepIndex": 0,
            "totalSteps": 0,
            "longInstruction": " Task complete!"
        })

    return JSONResponse({
        "status": "ok",
        "overlay": [{
            "bbox": None,
            "label": current_step["target_label"],
            "confidence": None,
            "instruction": current_step["title"],
        }],
        "stepIndex": task_manager.current_step,
        "totalSteps": task_manager.total_steps,
        "longInstruction": current_step.get("instruction", current_step["title"])
    })