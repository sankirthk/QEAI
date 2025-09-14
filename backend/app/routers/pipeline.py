from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
import cv2, numpy as np, json
from collections import deque

from app.models.detector import Detector
from app.models.task_manager import TaskManager
from app.models.vlm2 import plan

router = APIRouter()

detector = Detector(weights="app/ml/best.onnx", imgsz=640)
task_manager = TaskManager()

_detection_buffer = deque(maxlen=3)

def _labels_for_vlm(detections):
    out = []
    for d in detections:
        lbl = str(d.get("label", "")).strip().lower()
        if lbl:
            out.append({"label": lbl})
    return out

def _ensure_plan_from_state(detections, frame_np=None):
    if not task_manager.query or task_manager.plan:
        return
    vlm_buttons = _labels_for_vlm(detections)
    vlm_response = plan(task_manager.query, vlm_buttons, image_bgr=frame_np)

    steps_out = []
    for i, step in enumerate(vlm_response.get("steps", [])):
        steps_out.append({
            "index": i,
            "title": step.get("title", f"Step {i+1}"),
            "instruction": step.get("instruction", step.get("title", f"Step {i+1}")),
            "target_label": str(step.get("target_label", "")).strip().lower(),
        })

    if steps_out:
        task_manager.set_plan(task_manager.query, steps_out)

from fastapi import WebSocket, WebSocketDisconnect

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
                # Client disconnected while waiting
                print("WS runtime disconnect")
                break

            # --- TEXT message (instruction)
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

            # --- BINARY message (frame)
            elif "bytes" in message:
                frame_bytes = message["bytes"]
                nparr = np.frombuffer(frame_bytes, np.uint8)
                frame_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                detections = detector.detect(frame_np)

                # track detection buffer
                _detection_buffer.append(len(detections) >= 10)
                if len(_detection_buffer) > 3:
                    _detection_buffer.pop(0)

                # if ready → generate plan
                if (
                    task_manager.query
                    and not task_manager.plan
                    and len(_detection_buffer) == 3
                    and all(_detection_buffer)
                ):
                    _ensure_plan_from_state(detections, frame_np)

                # no detections
                if not detections:
                    if task_manager.plan:
                        long_instruction = "⚠️ No buttons detected. Please adjust the camera."
                    elif task_manager.query:
                        long_instruction = "⚠️ Looking for controls… please aim the camera at the panel."
                    else:
                        long_instruction = "⚠️ No buttons detected. Please enter a task and aim the camera."
                    await websocket.send_text(json.dumps({
                        "status": "no objects",
                        "overlay": [],
                        "stepIndex": task_manager.current_step,
                        "totalSteps": task_manager.total_steps,
                        "longInstruction": long_instruction,
                    }))
                    continue

                # still waiting for plan
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
                        "instruction": current_step["title"],
                    })

                long_instruction = current_step.get("instruction", f"Next: {current_step['title']}")

                await websocket.send_text(json.dumps({
                    "status": "ok",
                    "overlay": overlay,
                    "stepIndex": task_manager.current_step,
                    "totalSteps": task_manager.total_steps,
                    "longInstruction": long_instruction,
                }))

    except Exception as e:
        print(f"WS error: {e}")
    finally:
        await websocket.close()




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

    # Try to advance
    advanced = task_manager.complete_step()
    current_step = task_manager.get_current_instruction()

    if not advanced or not current_step:
        # Completed the last step
        task_manager.reset()
        return JSONResponse({
            "status": "done",
            "overlay": [],
            "stepIndex": 0,
            "totalSteps": 0,
            "longInstruction": "✅ Task complete!"
        })

    # Normal case → return the new current step
    overlay = [{"instruction": current_step["title"]}]

    return JSONResponse({
        "overlay": overlay,
        "stepIndex": task_manager.current_step,
        "totalSteps": task_manager.total_steps,
        "longInstruction": current_step.get("instruction", current_step["title"])
    })
