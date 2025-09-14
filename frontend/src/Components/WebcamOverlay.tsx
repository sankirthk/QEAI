import React from "react";
import "../Styles/WebcamOverlay.css";

interface OverlayData {
  x: number;
  y: number;
  width: number;
  height: number;
  instruction: string;
}

interface OverlayProps {
  overlays: OverlayData[];
}

const WebcamOverlay: React.FC<OverlayProps> = ({ overlays }) => {
  if (!overlays || overlays.length === 0) return null;

  return (
    <>
      {overlays.map((overlay, i) => {
        const colorClass = `neon-box color-${i % 4}`;
        return (
          <div
            key={i}
            className={colorClass}
            style={{
              top: overlay.y,
              left: overlay.x,
              width: overlay.width,
              height: overlay.height,
            }}
          >
            <p className={`neon-label color-${i % 4}`}>
              {overlay.instruction}
            </p>
          </div>
        );
      })}
    </>
  );
};

export default WebcamOverlay;
