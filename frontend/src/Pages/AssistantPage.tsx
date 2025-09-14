import React, { useState, Suspense } from "react";
import TaskInput from "../Components/TaskInput";
import WebcamFeed from "../Components/WebcamFeed";
import { House } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { LazyLaserFlow } from "./LandingPage";
import "../Styles/AssistantPage.css";

const AssistantPage: React.FC = () => {
  const navigate = useNavigate();
  const [task, setTask] = useState<string>("");

  return (
    <div className="assistant-page">
      {/* LaserFlow background */}
      <div className="assistant-bg">
        <Suspense fallback={null}>
          <LazyLaserFlow />
        </Suspense>
      </div>

      {/* Glass overlay */}
      <div className="assistant-glass">
        {/* Home icon */}
        <div className="ar__page-home">
          <House onClick={() => navigate("/")} />
        </div>

        {/* Hero text */}
        <div className="assistant-hero">
          <h1>Forge AR Assistant</h1>
          <p>
            Type your query and point your camera at the Instant Pot.
            <br />
            Follow the highlighted steps to complete your task.
          </p>
        </div>

        {/* Main content */}
        <div className="assistant-content">
          {!task ? (
            <TaskInput onStart={(t) => setTask(t)} />
          ) : (
            <WebcamFeed task={task} onStop={() => setTask("")} />
          )}
        </div>

        {/* Footer tip */}
        <div className="assistant-footer">
          💡 Tip: Keep the Instant Pot fully in view. All processing runs
          offline on your device.
        </div>
      </div>
    </div>
  );
};

export default AssistantPage;
