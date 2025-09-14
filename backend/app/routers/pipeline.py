from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
import cv2, numpy as np, json
from collections import deque

from app.models.detector import Detector
from app.models.task_manager import TaskManager
from app.models.vlm import plan

router = APIRouter()

detector = Detector(weights="app/ml/best.onnx", imgsz=640)
task_manager = TaskManager()

_detection_buffer = deque(maxlen=3)


# --- Helpers -----------------------------------------------------

def _labels_for_vlm(detections):
    """Extract button labels for LLM planning"""
    out = []
    for d in detections:
        lbl = str(d.get("label", "")).strip().lower()
        if lbl:
            out.append({"label": lbl})
    return out


def _ensure_plan_from_state(detections):
    """If we have a query but no plan, call the VLM/LLM to generate one"""
    if not task_manager.query or task_manager.plan:
        return
    vlm_buttons = _labels_for_vlm(detections)
    vlm_response = plan(task_manager.query, vlm_buttons)

    steps_out = []
    for i, step in enumerate(vlm_response.get("steps", [])):
        steps_out.append({
            "index": i,
            "title": step.get("title", f"Step {i+1}"),           # short
            "instruction": step.get("instruction", f"Step {i+1}"), # long
            "target_label": str(step.get("target_label", "")).strip().lower(),
        })

    if steps_out:
        task_manager.set_plan(task_manager.query, steps_out)


# --- WebSocket ---------------------------------------------------

@router.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            try:
                message = await websocket.receive()
            except WebSocketDisconnect:
                print("WS disconnected")
                break
            except RuntimeError:
                print("WS runtime disconnect")
                break

            # --- TEXT message (instruction from frontend) ---
            if "text" in message:
                try:
                    data = json.loads(message["text"])
                except Exception:
                    continue
                if data.get("type") == "instruction":
                    task_manager.query = data.get("task", "")
                    await websocket.send_text(
                        json.dumps({"status": "instruction_received"})
                    )

            # --- BINARY message (frame from webcam) ---
            elif "bytes" in message:
                frame_bytes = message["bytes"]
                nparr = np.frombuffer(frame_bytes, np.uint8)
                frame_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                detections = detector.detect(frame_np)

                # track detection buffer
                _detection_buffer.append(len(detections) >= 10)
                if len(_detection_buffer) > 3:
                    _detection_buffer.pop(0)

                # generate plan if ready
                if (
                    task_manager.query
                    and not task_manager.plan
                    and len(_detection_buffer) == 3
                    and all(_detection_buffer)
                ):
                    _ensure_plan_from_state(detections)

                # no detections
                if not detections:
                    if task_manager.plan:
                        li = "⚠️ No buttons detected. Please adjust the camera."
                    elif task_manager.query:
                        li = "⚠️ Looking for controls… please aim the camera at the panel."
                    else:
                        li = "⚠️ No buttons detected. Please enter a task and aim the camera."
                    await websocket.send_text(json.dumps({
                        "status": "no objects",
                        "overlay": [],
                        "stepIndex": task_manager.current_step,
                        "totalSteps": task_manager.total_steps,
                        "longInstruction": li,
                    }))
                    continue

                # waiting for plan
                if task_manager.query and not task_manager.plan:
                    await websocket.send_text(json.dumps({
                        "status": "waiting",
                        "overlay": [],
                        "stepIndex": 0,
                        "totalSteps": 0,
                        "longInstruction": "Align camera to show at least 10 buttons clearly.",
                    }))
                    continue

                # normal flow
                current_step = task_manager.get_current_instruction()
                if not current_step:
                    await websocket.send_text(json.dumps({
                        "status": "no active task",
                        "overlay": [],
                        "stepIndex": task_manager.current_step,
                        "totalSteps": task_manager.total_steps,
                        "longInstruction": "Enter a task to begin, then point the camera at the controls."
                    }))
                    continue

                target = current_step["target_label"]
                matches = [d for d in detections if str(d["label"]).strip().lower() == target]
                best_det = max(matches, key=lambda d: d["confidence"], default=None)

                overlay = []
                if best_det:
                    overlay.append({
                        "bbox": best_det["bbox"],
                        "label": best_det["label"],
                        "confidence": best_det["confidence"],
                        "instruction": current_step["title"],   # short for overlay
                    })

                long_instruction = current_step.get("instruction", f"Next: {current_step['title']}")
                await websocket.send_text(json.dumps({
                    "status": "ok",
                    "overlay": overlay,
                    "stepIndex": task_manager.current_step,
                    "totalSteps": task_manager.total_steps,
                    "longInstruction": long_instruction,       # long for UI paragraph
                }))

    except Exception as e:
        print(f"WS error: {e}")
    finally:
        try:
            if not websocket.client_state.DISCONNECTED:
                await websocket.close()
        except Exception as close_error:
            print(f"Error closing websocket: {close_error}")


# --- Step complete -----------------------------------------------

@router.post("/step_complete")
async def step_complete():
    # If no plan or already complete
    if not task_manager.plan or task_manager.current_step >= task_manager.total_steps:
        task_manager.reset()
        return JSONResponse({
            "status": "done",
            "overlay": [],
            "stepIndex": 0,
            "totalSteps": 0,
            "longInstruction": "✅ Task complete!"
        })

    # Advance step
    advanced = task_manager.complete_step()
    current_step = task_manager.get_current_instruction()

    if not advanced or not current_step:
        task_manager.reset()
        return JSONResponse({
            "status": "done",
            "overlay": [],
            "stepIndex": 0,
            "totalSteps": 0,
            "longInstruction": "✅ Task complete!"
        })

    # Overlay still shows short title
    overlay = [{
        "bbox": None,  # we don’t have fresh detections here
        "label": current_step["target_label"],
        "confidence": None,
        "instruction": current_step["title"],   # short for box
    }]

    return JSONResponse({
        "status": "ok",
        "overlay": overlay,
        "stepIndex": task_manager.current_step,
        "totalSteps": task_manager.total_steps,
        "longInstruction": current_step.get("instruction", current_step["title"]) # long for paragraph
    })
