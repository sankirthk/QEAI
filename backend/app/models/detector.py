import cv2
from ultralytics import YOLO

class Detector:
    def __init__(self, weights="app/ml/best.pt", imgsz=640):
        self.model = YOLO(weights)
        self.imgsz = imgsz

    def detect(self, frame):
        orig_h, orig_w = frame.shape[:2]
        results = self.model.predict(frame, imgsz=self.imgsz, conf=0.25)

        detections = []
        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                conf = float(box.conf)
                cls_id = int(box.cls)
                label = self.model.names[cls_id]

                # Clamp to original frame size
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(orig_w, x2), min(orig_h, y2)

                detections.append({
                    "label": label,
                    "confidence": conf,
                    "bbox": [x1, y1, x2, y2]  # in original frame coords
                })
        return detections