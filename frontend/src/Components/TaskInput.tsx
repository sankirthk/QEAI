import React, { useState, useEffect } from "react";

const PLACEHOLDER_ARRAY = [
  "Start with your Instant Pot goal (e.g., Cook rice)",
  "What should I help you make today?",
  "Enter your first instruction (e.g., Pressure Cook beans)",
  "Your Instant Pot assistant is ready — what’s the plan?",
];

interface TaskInputProps {
  onStart: (task: string) => void;
}

const TaskInput: React.FC<TaskInputProps> = ({ onStart }) => {
  const [placeholder, setPlaceholder] = useState(PLACEHOLDER_ARRAY[0]);
  const [input, setInput] = useState("");

  useEffect(() => {
    let i = 0;
    const interval = setInterval(() => {
      i = (i + 1) % PLACEHOLDER_ARRAY.length;
      setPlaceholder(PLACEHOLDER_ARRAY[i]);
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const handleStart = () => {
    if (input.trim()) {
      onStart(input.trim());
    }
  };

  return (
    <div className="ti__component-container">
      <div className="ti__component-controls">
        <input
          id="textbox"
          className="ti__component-controls-textbox"
          type="text"
          placeholder={placeholder}
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
        <button className="glow-button" onClick={handleStart}>
          Start Task
        </button>
      </div>
    </div>
  );
};

export default TaskInput;
