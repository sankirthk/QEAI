import React, { useState, useEffect, useRef } from "react";
import Webcam from "react-webcam";
import axios from "axios";
import WebcamOverlay from "./WebcamOverlay";
import "../Styles/TaskInput.css";
import InstantPotHUD from "./InstantPotHUD"; //

const STREAM_INTERVAL_MS = 1000; // ~1 fps
const videoConstraints = { facingMode: "environment" };
const BACKEND_URL = "https://192.168.137.1:8000";

interface OverlayData {
  bbox?: [number, number, number, number];
  label?: string;
  confidence?: number;
  instruction?: string; // short overlay instruction
}

interface WebcamFeedProps {
  task: string;
  onStop: () => void;
}

const isNum = (v: any): v is number =>
  typeof v === "number" && !Number.isNaN(v);

const WebcamFeed: React.FC<WebcamFeedProps> = ({ task, onStop }) => {
  const [streaming, setStreaming] = useState(true);
  const [instructionSent, setInstructionSent] = useState(false);
  const [overlays, setOverlays] = useState<OverlayData[]>([]);
  const [currentStep, setCurrentStep] = useState(0);
  const [totalSteps, setTotalSteps] = useState(0);
  const [longInstruction, setLongInstruction] = useState(""); // wordier text
  const [taskComplete, setTaskComplete] = useState(false);
  const [hasBBox, setHasBBox] = useState(false); //
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

        // Send task only once at the start
        if (task && !instructionSent) {
          formData.append("instruction", task);
          setInstructionSent(true);
        }

        const res = await axios.post(`${BACKEND_URL}/api/stream`, formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });

        if (res.data) {
          const {
            overlay,
            stepIndex,
            totalSteps: ts,
            longInstruction: li,
            status,
          } = res.data;

          if (status === "no objects") {
            setOverlays([]);
            setHasBBox(false); // nothing detected
            setLongInstruction(
              "⚠️ No buttons detected. Please adjust the camera."
            );
            setTaskComplete(false);
            return;
          }

          // Normal update path
          setOverlays(Array.isArray(overlay) ? overlay : []);

          if (Array.isArray(overlay) && overlay.length > 0) {
            setHasBBox(true); // ✅ Lock HUD once we have bbox
          }

          if (isNum(stepIndex)) setCurrentStep(stepIndex);
          if (isNum(ts)) setTotalSteps(ts);
          if (typeof li === "string") setLongInstruction(li);

          if (status === "done") {
            setStreaming(false);
            setTaskComplete(true);
            return;
          }

          if (isNum(stepIndex) && isNum(ts) && ts > 0 && stepIndex >= ts) {
            setStreaming(false);
            setTaskComplete(true);
            return;
          }
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
      const res = await axios.post(`${BACKEND_URL}/api/step_complete`);
      if (res.data) {
        const {
          overlay,
          stepIndex,
          totalSteps: ts,
          longInstruction: li,
          status,
        } = res.data;

        if (status === "no objects") {
          setOverlays([]);
          setHasBBox(false);
          setLongInstruction(
            "⚠️ No buttons detected. Please adjust the camera."
          );
          setTaskComplete(false);
        } else {
          setOverlays(Array.isArray(overlay) ? overlay : []);

          if (Array.isArray(overlay) && overlay.length > 0) {
            setHasBBox(true);
          }

          if (isNum(stepIndex)) setCurrentStep(stepIndex);
          if (isNum(ts)) setTotalSteps(ts);
          if (typeof li === "string") setLongInstruction(li);

          if (status === "done") {
            setStreaming(false);
            setTaskComplete(true);
            return;
          }

          if (isNum(stepIndex) && isNum(ts) && ts > 0 && stepIndex >= ts) {
            setStreaming(false);
            setTaskComplete(true);
            return;
          }
        }
      }
    } catch (err) {
      console.error("Error marking step complete:", err);
    }
  };

  // Stop task manually
  const handleStopTask = () => {
    setStreaming(false);
    setOverlays([]);
    setCurrentStep(0);
    setTotalSteps(0);
    setInstructionSent(false);
    setLongInstruction("");
    setTaskComplete(false);
    setHasBBox(false); // reset HUD
    onStop();
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

        {/* overlays */}
        <div style={{ position: "absolute", inset: 0 }}>
          <WebcamOverlay
            overlays={overlays.map((ov) => {
              const videoEl = webcamRef.current?.video as
                | HTMLVideoElement
                | undefined;
              const videoWidth = videoEl?.videoWidth || 640;
              const videoHeight = videoEl?.videoHeight || 640;

              const scaleX = videoWidth / 640;
              const scaleY = videoHeight / 640;

              if (!ov.bbox) {
                return {
                  x: 0,
                  y: videoHeight - 50,
                  width: videoWidth,
                  height: 40,
                  instruction: ov.instruction || ov.label || "",
                };
              }

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

          {/* 🚀 HUD */}
          <InstantPotHUD locked={hasBBox} />
        </div>
      </div>

      <div className="ti__component-controls">
        <button className="glow-button" onClick={handleStopTask}>
          Stop Task
        </button>

        {!taskComplete && currentStep < totalSteps && (
          <button
            className="glow-button"
            onClick={handleDone}
            style={{ marginTop: "1rem", padding: "10px 20px" }}
          >
            Done
          </button>
        )}

        {longInstruction && !taskComplete && (
          <p
            style={{
              marginTop: "1rem",
              fontSize: "1rem",
              color: longInstruction.startsWith("⚠️") ? "orange" : "white",
              textAlign: "center",
              maxWidth: "400px",
            }}
          >
            {longInstruction}
          </p>
        )}

        {taskComplete && (
          <p
            style={{
              marginTop: "1rem",
              fontSize: "1.2rem",
              fontWeight: "bold",
              color: "#00ff88",
              textAlign: "center",
            }}
          >
            Task complete!
          </p>
        )}
      </div>
    </div>
  );
};

export default WebcamFeed;
