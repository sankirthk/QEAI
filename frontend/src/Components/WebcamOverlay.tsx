import React from "react";

interface OverlayData {
  x: number;
  y: number;
  width: number;
  height: number;
  instruction: string;
}

interface OverlayProps {
  overlays: OverlayData[]; // now supports multiple overlays
}

const WebcamOverlay: React.FC<OverlayProps> = ({ overlays }) => {
  if (!overlays || overlays.length === 0) return null;

  return (
    <>
      {overlays.map((overlay, i) => (
        <div
          key={i}
          style={{
            position: "absolute",
            top: overlay.y,
            left: overlay.x,
            width: overlay.width,
            height: overlay.height,
            border: "2px solid red",
            pointerEvents: "none",
          }}
        >
          <p
            style={{
              position: "absolute",
              top: "-1.5rem",
              left: 0,
              background: "red",
              color: "white",
              padding: "2px 4px",
              fontSize: "0.8rem",
            }}
          >
            {overlay.instruction}
          </p>
        </div>
      ))}
    </>
  );
};

export default WebcamOverlay;
