import React, { useState } from "react";
import TaskInput from "../Components/TaskInput";
import WebcamFeed from "../Components/WebcamFeed";
import "../Styles/AssistantPage.css";
import { House } from "lucide-react";
import { useNavigate } from "react-router-dom";

const AssistantPage: React.FC = () => {
  const navigate = useNavigate();
  const [task, setTask] = useState<string>("");

  return (
    <>
      <div className="ar__page-home">
        <House onClick={() => navigate("/")} />
      </div>
      <div className="ar__page-container">
        {!task ? (
          <TaskInput onStart={(t) => setTask(t)} />
        ) : (
          <WebcamFeed task={task} onStop={() => setTask("")} />
        )}
      </div>
    </>
  );
};

export default AssistantPage;
