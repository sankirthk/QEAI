from pydantic import BaseModel
from typing import List, Optional

class Detection(BaseModel):
    label: str
    confidence: float
    bbox: List[float]   # [x1, y1, x2, y2]
    track_id: Optional[int] = None

class DetectionResponse(BaseModel):
    detections: List[Detection]