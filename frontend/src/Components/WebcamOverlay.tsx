import React from "react";
import "../Styles/WebcamOverlay.css";

interface OverlayData {
  bbox?: [number, number, number, number]; // already in original frame coords
  label?: string;
  instruction?: string;
}

interface OverlayProps {
  overlays: OverlayData[];
  videoWidth: number;
  videoHeight: number;
}

const WebcamOverlay: React.FC<OverlayProps> = ({ overlays }) => {
  if (!overlays || overlays.length === 0) return null;

  return (
    <>
      {overlays.map((ov, i) => {
        if (!ov.bbox) return null;

        const [x1, y1, x2, y2] = ov.bbox;
        const width = x2 - x1;
        const height = y2 - y1;

        return (
          <div
            key={i}
            className={`neon-box color-${i % 4}`}
            style={{
              position: "absolute",
              top: y1,
              left: x1,
              width,
              height,
            }}
          >
            <p className={`neon-label color-${i % 4}`}>
              {ov.instruction || ov.label || ""}
            </p>
          </div>
        );
      })}
    </>
  );
};

export default WebcamOverlay;