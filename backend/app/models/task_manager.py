class TaskManager:
    def __init__(self):
        self.reset()

    def reset(self):
        self.query = None
        # plan = list of {"step": str, "button_label": str, "long_step": Optional[str]}
        self.plan = []
        self.current_step = 0
        self.total_steps = 0
        self.active_button_label = None

    def set_plan(self, query: str, plan: list):
        """
        Store a new task plan (sequence of steps).
        Each step can contain:
          - step: short text for overlays
          - long_step: optional longer text for explanation
          - button_label: identifier for target button
        """
        self.query = query
        self.plan = plan
        self.total_steps = len(plan)
        self.current_step = 0
        self.active_button_label = (
            plan[0]["button_label"] if plan else None
        )

    def get_current_instruction(self):
        """
        Return the current step dict, or None if task is finished.
        Always ensures 'long_step' exists (fallback to 'step').
        """
        if not self.plan or self.current_step >= self.total_steps:
            return None

        step = self.plan[self.current_step]

        # ensure long_step fallback
        if "long_step" not in step or not step["long_step"]:
            step["long_step"] = step["step"]

        return step

    def complete_step(self):
        """
        Advance to the next step.
        Returns True if there are more steps, False if finished.
        """
        if self.current_step < self.total_steps - 1:
            self.current_step += 1
            self.active_button_label = self.plan[self.current_step]["button_label"]
            return True
        # Finished all steps
        self.active_button_label = None
        return False
