import cv2
import numpy as np
import onnxruntime as ort

class Detector:
    def __init__(self, weights="app/ml/best.onnx", imgsz=640, conf_thres=0.25, use_qnn=True):
        self.imgsz = imgsz
        self.conf_thres = conf_thres

        if use_qnn:
            try:
                execution_provider_option = {
                    "backend_path": "QnnHtp.dll",
                    "enable_htp_fp16_precision": "1",
                    "htp_performance_mode": "high_performance"
                }
                self.session = ort.InferenceSession(
                    weights,
                    providers=[("QNNExecutionProvider", execution_provider_option),
                               "CPUExecutionProvider"]
                )
                print("[Detector] Using QNNExecutionProvider with CPU fallback")
            except Exception as e:
                print(f"[Detector] QNN init failed: {e}, falling back to CPU")
                self.session = ort.InferenceSession(weights, providers=["CPUExecutionProvider"])
        else:
            self.session = ort.InferenceSession(weights, providers=["CPUExecutionProvider"])
            print("[Detector] Using CPUExecutionProvider")

        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name

        self.names = {
            0: 'cancel', 1: 'decrease', 2: 'increase', 3: 'keep_warm',
            4: 'lid_open', 5: 'pressure', 6: 'pressure_cook', 7: 'rice',
            8: 'saute', 9: 'start', 10: 'steam', 11: 'temp_set'
        }

    def preprocess(self, frame):
        img = cv2.resize(frame, (self.imgsz, self.imgsz))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        img = np.transpose(img, (2, 0, 1))[None]  # (1,3,H,W)
        return img

    def detect(self, frame):
        inp = self.preprocess(frame)
        preds = self.session.run([self.output_name], {self.input_name: inp})[0]

        preds = np.squeeze(preds)

        detections = []
        for i, det in enumerate(preds):
            if len(det) >= 6:
                x1, y1, x2, y2, score, cls_id = det[:6]
                if score >= self.conf_thres:
                    detections.append({
                        "label": self.names.get(int(cls_id), str(int(cls_id))),
                        "confidence": float(score),
                        "bbox": [int(x1), int(y1), int(x2), int(y2)],
                        "track_id": i
                    })
        return detections
