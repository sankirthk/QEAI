import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import "../Styles/InstantPotHUD.css";

interface Props {
  locked: boolean;
}

const InstantPotHUD: React.FC<Props> = ({ locked }) => {
  const [flash, setFlash] = useState(false);

  // Trigger flash spotlight effect when locked first becomes true
  useEffect(() => {
    if (locked) {
      setFlash(true);
      const timer = setTimeout(() => setFlash(false), 1000); // spotlight lasts 1s
      return () => clearTimeout(timer);
    }
  }, [locked]);

  return (
    <div className="hud-container">
      {/* Idle scanning line */}
      {!locked && <div className="hud-scanline" />}

      {/* Spotlight flash effect */}
      <AnimatePresence>
        {flash && (
          <motion.div
            initial={{ opacity: 1 }}
            animate={{ opacity: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 1 }}
            className="hud-spotlight"
          />
        )}
      </AnimatePresence>

      {/* Locked Label */}
      {locked && !flash && (
        <div className="hud-locked-label">POT LOCKED ✅</div>
      )}
    </div>
  );
};

export default InstantPotHUD;
