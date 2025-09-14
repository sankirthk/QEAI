import React from "react";
import TaskInput from "../Components/TaskInput";
import WebcamFeed from "../Components/WebcamFeed";
import { useAssistantStore } from "../Store/assistantStore";
import "../Styles/AssistantPage.css";
import { House } from "lucide-react";
import { useNavigate } from "react-router-dom";

const AssistantPage: React.FC = () => {
  const navigate = useNavigate();
  const task = useAssistantStore((s) => s.task);

  return (
    <>
      <div className="ar__page-home">
        <House onClick={() => navigate("/")} />
      </div>
      <div className="ar__page-container">
        {!task ? <TaskInput /> : <WebcamFeed />}
      </div>
    </>
  );
};

export default AssistantPage;
