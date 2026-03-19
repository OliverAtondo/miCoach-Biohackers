import { useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import api from "../api/client";
import { useAuth } from "../contexts/AuthContext";
import "./Onboarding.css";

export default function Onboarding() {
  const { user, refreshUser } = useAuth();
  const navigate = useNavigate();
  
  const [phase, setPhase] = useState("analyzing"); // analyzing | suggestions | finalizing | done | error
  const [error, setError] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [showAllRoles, setShowAllRoles] = useState(false);
  const [finalCareer, setFinalCareer] = useState("");

  useEffect(() => {
    if (user?.onboarding_complete) {
      navigate("/dashboard");
      return;
    }

    if (user?.onboarding_answers) {
      try {
        const answers = JSON.parse(user.onboarding_answers);
        getSuggestions(answers);
      } catch (e) {
        setError("Could not parse your onboarding answers.");
        setPhase("error");
      }
    } else if (user) {
        // If we have a user but no answers, something went wrong in registration
        setError("Onboarding questionnaire was not completed during registration.");
        setPhase("error");
    }
  }, [user, navigate]);

  const getSuggestions = async (answers) => {
    setPhase("analyzing");
    try {
      const res = await api.post("/api/mentor/suggest-roles", answers);
      setSuggestions(res.data?.roles || []);
      setPhase("suggestions");
    } catch (err) {
      setError(err.response?.data?.detail || "Could not get career recommendations.");
      setPhase("error");
    }
  };

  const finalizeOnboarding = async () => {
    if (!finalCareer) return;
    setPhase("finalizing");
    try {
      await api.post("/api/mentor/onboard", { chosen_role: finalCareer });
      await refreshUser(); // This will set onboarding_complete to true
      setPhase("done");
      setTimeout(() => navigate("/dashboard"), 1500);
    } catch (err) {
      setError(err.response?.data?.detail || "Something went wrong. Please try again.");
      setPhase("error");
    }
  };

  const renderSuggestions = () => {
    const initialRole = user?.career_path;
    let displaySuggestions = showAllRoles ? suggestions : suggestions.slice(0, 5);
    // Ensure initial role isn't duplicated if it also appears in AI suggestions
    if (initialRole && displaySuggestions.includes(initialRole)) {
        displaySuggestions = displaySuggestions.filter(r => r !== initialRole);
    }

    return (
      <>
        <h2>Final Career Selection</h2>
        <p>Our AI has recommendations, but the choice is yours. Select your definitive career path.</p>
        
        <div className="suggestions">
          {/* User's initial choice */}
          {initialRole && initialRole !== "None of the above" && (
             <div 
                key={initialRole}
                className={`role-card ${finalCareer === initialRole ? 'selected' : ''}`}
                onClick={() => setFinalCareer(initialRole)}
            >
                <div className="role-title">{initialRole}</div>
                <div className="role-sub">Your Current Selection</div>
            </div>
          )}

          {/* AI Suggestions */}
          {displaySuggestions.map((r, i) => (
            <div key={r} className={`role-card ${finalCareer === r ? 'selected' : ''}`} onClick={() => setFinalCareer(r)}>
              <div className="role-title">{r}</div>
              <div className="role-sub">AI Recommendation #{i + 1}</div>
            </div>
          ))}
        </div>

        <div style={{ marginTop: 16, display: 'flex', justifyContent: 'center', gap: '1rem' }}>
            {!showAllRoles && suggestions.length > 5 && (
                <button className="btn-secondary" onClick={() => setShowAllRoles(true)}>Show All Suggestions</button>
            )}
            <button className="btn-primary" disabled={!finalCareer} onClick={finalizeOnboarding}>Confirm & Build My Roadmap</button>
        </div>
      </>
    )
  }

  return (
    <div className="onboarding-container">
      <div className="onboarding-card">
        <div className="onboarding-logo">MC</div>

        {(phase === "analyzing" || phase === "finalizing") && (
          <>
            <div className="spinner" />
            <h2>{phase === 'finalizing' ? 'Building Your Roadmap...' : 'Analyzing Your Profile...'}</h2>
            <p>{phase === 'finalizing' 
                ? 'Your mentor is preparing your personalized learning path.' 
                : 'We are processing your questionnaire to suggest the best career paths for you.'}
            </p>
          </>
        )}

        {phase === "suggestions" && renderSuggestions()}

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
          </>
        )}
      </div>
    </div>
  );
}
