import numpy as np
import supervision as sv

class Tracker:
    def __init__(self):
        self.tracker = sv.ByteTrack()

    def track(self, detections):
        """
        detections: list of dicts with keys 'bbox', 'label', 'confidence'
        returns: list of dicts with tracking info
        """
        if not detections:
            return []

        xyxy = []
        confidences = []
        class_ids = []

        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            xyxy.append([x1, y1, x2, y2])
            confidences.append(det["confidence"])
            # if you want to map labels to ints, do it here
            class_ids.append(0)  # or map with a label→id dict

        sv_dets = sv.Detections(
            xyxy=np.array(xyxy, dtype=float),
            confidence=np.array(confidences, dtype=float),
            class_id=np.array(class_ids, dtype=int),
        )

        tracked = self.tracker.update_with_detections(sv_dets)

        # Convert back to list of dicts (matching your pipeline’s expected format)
        outputs = []
        for i, box in enumerate(tracked.xyxy):
            outputs.append({
                "bbox": box.astype(int).tolist(),
                "confidence": float(tracked.confidence[i]),
                "track_id": int(tracked.tracker_id[i]),
                "label": str(tracked.class_id[i]),
            })

        return outputs
