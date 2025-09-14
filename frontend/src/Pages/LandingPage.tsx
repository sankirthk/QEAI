import React, { Suspense } from "react";
import TextType from "../Components/UI/TextType";
import { useNavigate } from "react-router-dom";
import "../Styles/LandingPage.css";

const LazyLaserFlow = React.lazy(() => import("../Components/UI/LaserFlow"));

const LandingPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="landing__page-container">
      {/* Background */}
      <div className="landing__page-background">
        {/* <Suspense fallback={null}>
          <LazyLaserFlow />
        </Suspense> */}
      </div>

      {/* Foreground content */}
      <div className="landing__page-foreground">
        {/* Hero Section */}

        <section className="landing__page-hero-section">
          <TextType
            className="landing__page-title"
            text={["FORGE AR"]}
            typingSpeed={100}
            pauseDuration={1000}
            showCursor={true}
            cursorCharacter="_"
          />
          <h3 className="landing__page-tag-line">
            Real-time guidance, right at the edge
          </h3>
        </section>

        {/* About Section */}
        <section className="landing__page-about-section">
          <h2>Overview</h2>
          <div className="about__content">
            <div className="about__card">
              Across industries such as energy, manufacturing, and
              transportation, critical expertise is being lost as experienced
              workers retire and fewer new workers enter the field. Training new
              operators quickly, safely, and effectively is a growing
              challenge—especially in environments where internet connectivity
              is unreliable or unavailable.
            </div>
            <div className="about__card">
              Our project addresses this by creating an{" "}
              <strong>AR-guided assistant powered by Edge AI</strong>. The
              system delivers real-time visual overlays, step-by-step
              instructions, and contextual safety guidance—running fully offline
              on a Snapdragon X Copilot+ PC.
            </div>
            <div className="about__card">
              For the hackathon, we demonstrate the concept on a
              <strong> household Instant Pot</strong>. While low-stakes, it
              serves as a relatable stand-in for complex industrial equipment,
              allowing us to showcase AR overlays, AI-driven recognition, and
              offline inference in a safe, accessible setting. The same
              framework can be extended to high-stakes training environments
              such as oil rigs, power plants, or factory floors.
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="landing__page-cta-section">
          <h2>Ready to try it out?</h2>
          <button
            className="glow-button"
            onClick={() => navigate("/assistant")}
          >
            ACTIVATE FORGE
          </button>
        </section>
      </div>
    </div>
  );
};

export default LandingPage;
