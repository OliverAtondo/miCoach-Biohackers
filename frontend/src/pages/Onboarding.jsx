import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api/client";
import { useAuth } from "../contexts/AuthContext";
import "./Onboarding.css";

export default function Onboarding() {
  const { user, refreshUser } = useAuth();
  const navigate = useNavigate();
  const [phase, setPhase] = useState("analyzing"); // analyzing | generating | done | error
  const [error, setError] = useState("");

  useEffect(() => {
    if (user?.onboarding_complete) {
      navigate("/dashboard");
      return;
    }
    runOnboarding();
  }, []);

  const runOnboarding = async () => {
    try {
      setPhase("analyzing");
      await api.post("/api/mentor/onboard");
      setPhase("done");
      await refreshUser();
      setTimeout(() => navigate("/dashboard"), 1500);
    } catch (err) {
      setError(err.response?.data?.detail || "Something went wrong. Please try again.");
      setPhase("error");
    }
  };

  return (
    <div className="onboarding-container">
      <div className="onboarding-card">
        <div className="onboarding-logo">MC</div>

        {phase === "analyzing" && (
          <>
            <div className="spinner" />
            <h2>Analyzing your profile...</h2>
            <p>Your mentor is reviewing your CV and GitHub projects to understand your current level.</p>
            <div className="progress-steps">
              <div className="progress-step active">Reading CV</div>
              <div className="progress-step active">Fetching GitHub repos</div>
              <div className="progress-step">Generating analysis</div>
              <div className="progress-step">Building your roadmap</div>
            </div>
          </>
        )}

        {phase === "done" && (
          <>
            <div className="success-icon">✓</div>
            <h2>Your mentor is ready!</h2>
            <p>Redirecting to your dashboard...</p>
          </>
        )}

        {phase === "error" && (
          <>
            <div className="error-icon">!</div>
            <h2>Something went wrong</h2>
            <p>{error}</p>
            <button className="btn-primary" onClick={runOnboarding}>Try Again</button>
          </>
        )}
      </div>
    </div>
  );
}
