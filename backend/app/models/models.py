from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class Button(BaseModel):
    label: str
    conf: float
    bbox_xyxy: List[int] = Field(min_length=4, max_length=4)


class Step(BaseModel):
    index: int
    title: str
    instruction: str
    target_label: str


class StepHistoryItem(BaseModel):
    step: int
    button_label: str


class StepState(BaseModel):
    task_id: str
    user_goal: str
    frame_seq: int
    step_index: int
    buttons: List[Button]
    steps: List[Step]
    history: List[StepHistoryItem] = []
    plan_cache_id: Optional[str] = None


class FrameIn(BaseModel):
    frame_seq: int
    image_b64: str
    user_goal: Optional[str] = None
    user_event: Optional[Literal["step_done"]] = None


class RenderOut(BaseModel):
    frame_seq: int
    step_index: int
    step: Step
    ui_hint: str | None = None


class ClarifyOut(BaseModel):
    status: Literal["needs_clarification"]
    reason: str
    suggestion: str
