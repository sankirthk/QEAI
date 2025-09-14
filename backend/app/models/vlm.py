class VLM:
    def __init__(self):
        pass

    def plan(self, detections, instruction: str):
        """
        Mock VLM planner.
        Given a user query (e.g., "Make rice"), decide all steps.
        Uses labels only (no track_id).
        Each step includes:
          - step: short text for overlay
          - long_step: longer, wordier instruction
          - button_label: target button
        """

        # Example: user says "Make rice"
        if "rice" in instruction.lower():
            return [
                {
                    "step": "Press Rice",
                    "long_step": "Now press the Rice button on your Instant Pot to begin cooking.",
                    "button_label": "rice",
                },
                {
                    "step": "Press Start",
                    "long_step": "After selecting Rice, press the Start button to start the cooking process.",
                    "button_label": "start",
                },
            ]

        # Fallback mock plan
        return [
            {
                "step": "Press Pressure Cook",
                "long_step": "Select the Pressure Cook button to prepare for cooking under pressure.",
                "button_label": "pressure_cook",
            }
        ]
