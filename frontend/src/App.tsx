import React from "react";
import { Routes, Route } from "react-router-dom";
import LandingPage from "./Pages/LandingPage";
import AssistantPage from "./Pages/AssistantPage";

function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/assistant" element={<AssistantPage />} />
    </Routes>
  );
}

export default App;
