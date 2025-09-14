import React, { useState, useEffect, useRef } from "react";
import Webcam from "react-webcam";
import axios from "axios";
import WebcamOverlay from "./WebcamOverlay";
import "../Styles/TaskInput.css";

const STREAM_INTERVAL_MS = 1000; // ~2 fps
const videoConstraints = { facingMode: "environment" };
const BACKEND_URL = "https://192.168.1.230:8000";

interface OverlayData {
  bbox: [number, number, number, number]; // [x1, y1, x2, y2]
  label?: string;
  confidence?: number;
  instruction?: string;
}

const WebcamFeed: React.FC = () => {
  const [streaming, setStreaming] = useState(true);
  const [instructionSent, setInstructionSent] = useState(false);
  const [overlays, setOverlays] = useState<OverlayData[]>([]);
  const [currentStep, setCurrentStep] = useState(0);
  const [totalSteps, setTotalSteps] = useState(0);
  const [task, setTask] = useState(""); // optional: can come from props
  const webcamRef = useRef<Webcam>(null);

  // Continuous streaming loop
  useEffect(() => {
    if (!streaming || !webcamRef.current) return;

    const interval = setInterval(async () => {
      const imageSrc = webcamRef.current?.getScreenshot();
      if (!imageSrc) return;

      try {
        const blob = await (await fetch(imageSrc)).blob();
        const formData = new FormData();
        formData.append("frame", blob, "frame.jpg");

        // ✅ Only send instruction once per task
        if (task && !instructionSent) {
          formData.append("instruction", task);
          setInstructionSent(true);
        }

        const res = await axios.post(`${BACKEND_URL}/api/stream`, formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });

        if (res.data) {
          setOverlays(res.data.overlay || []);
          if (res.data.stepIndex !== undefined)
            setCurrentStep(res.data.stepIndex);
          if (res.data.totalSteps !== undefined)
            setTotalSteps(res.data.totalSteps);
        }
      } catch (err) {
        console.error("Streaming error:", err);
      }
    }, STREAM_INTERVAL_MS);

    return () => clearInterval(interval);
  }, [streaming, task, instructionSent]);

  // Done → advance step
  const handleDone = async () => {
    try {
      const res = await axios.post(`${BACKEND_URL}/api/step_complete`, {
        currentStep,
      });
      if (res.data) {
        setOverlays(res.data.overlay || []);
        if (res.data.stepIndex !== undefined)
          setCurrentStep(res.data.stepIndex);
        if (res.data.totalSteps !== undefined)
          setTotalSteps(res.data.totalSteps);

        setInstructionSent(false);
      }
    } catch (err) {
      console.error("Error marking step complete:", err);
    }
  };

  // Stop task → cleanup
  const handleStopTask = () => {
    setStreaming(false);
    setOverlays([]);
    setCurrentStep(0);
    setTotalSteps(0);
    setTask("");
    setInstructionSent(false);
  };

  return (
    <div className="ti__component-container">
      <div style={{ position: "relative" }}>
        <Webcam
          className="ti__component-webcam"
          ref={webcamRef}
          audio={false}
          videoConstraints={videoConstraints}
          screenshotFormat="image/jpeg"
        />

        {/* overlays drawn on top of webcam */}
        <div style={{ position: "absolute", inset: 0 }}>
        <WebcamOverlay
    overlays={overlays.map((ov) => {
      const videoEl = webcamRef.current?.video as HTMLVideoElement | undefined;
      const videoWidth = videoEl?.videoWidth || 640;
      const videoHeight = videoEl?.videoHeight || 640;

      const scaleX = videoWidth / 640;
      const scaleY = videoHeight / 640;

      const [x1, y1, x2, y2] = ov.bbox;

      return {
        x: x1 * scaleX,
        y: y1 * scaleY,
        width: (x2 - x1) * scaleX,
        height: (y2 - y1) * scaleY,
        instruction: ov.instruction || ov.label || "",
      };
    })}
  />
</div>
      </div>

      <div className="ti__component-controls">
        <button className="glow-button" onClick={handleStopTask}>
          Stop Task
        </button>

        {currentStep < totalSteps && (
          <button
            className="glow-button"
            onClick={handleDone}
            style={{ marginTop: "1rem", padding: "10px 20px" }}
          >
            Done
          </button>
        )}
      </div>
    </div>
  );
};

export default WebcamFeed;
