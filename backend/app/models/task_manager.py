# class TaskManager:
#     def __init__(self):
#         self.reset()

#     def reset(self):
#         self.query = None
#         # plan = list of {"short_step": str, "long_step": str, "button_label": str}
#         self.plan = []
#         self.current_step = 0
#         self.total_steps = 0
#         self.active_button_label = None

#     def set_plan(self, query: str, plan: list):
#         """
#         Store a new task plan (sequence of steps).
#         """
#         self.query = query
#         self.plan = plan
#         self.total_steps = len(plan)
#         self.current_step = 0
#         self.active_button_label = plan[0]["button_label"] if plan else None

#     def get_current_instruction(self):
#         """
#         Return the current step dict, or None if finished.
#         """
#         if not self.plan or self.current_step >= self.total_steps:
#             return None
#         return self.plan[self.current_step]

#     def complete_step(self):
#         """
#         Advance to the next step.
#         Returns True if there are more steps, False if finished.
#         """
#         if self.current_step < self.total_steps - 1:
#             self.current_step += 1
#             self.active_button_label = self.plan[self.current_step]["button_label"]
#             return True
#         # Finished all steps
#         self.active_button_label = None
#         return False


class TaskManager:
    def __init__(self):
        self.reset()

    def reset(self):
        self.query: str | None = None
        self.plan: list[dict] = []  # list of Step dicts
        self.current_step: int = 0
        self.total_steps: int = 0

    def set_plan(self, query: str, plan: list[dict]):
        """
        Store a new task plan (sequence of steps).
        Each step must conform to Step schema:
        { index:int, title:str, instruction:str, target_label:str }
        """
        self.query = query
        self.plan = plan
        self.total_steps = len(plan)
        self.current_step = 0

    def get_current_instruction(self) -> dict | None:
        """
        Return the current step dict, or None if finished.
        """
        if not self.plan or self.current_step >= self.total_steps:
            return None
        return self.plan[self.current_step]

    def complete_step(self) -> bool:
        """
        Advance to the next step.
        Returns True if there are more steps, False if finished.
        """
        if self.current_step < self.total_steps - 1:
            self.current_step += 1
            return True
        return False

