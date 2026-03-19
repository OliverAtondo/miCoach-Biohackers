import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api/client";
import { useAuth } from "../contexts/AuthContext";
import OnboardingQuestions from "../components/OnboardingQuestions";
import "./Onboarding.css";

export default function Onboarding() {
  const { user, refreshUser } = useAuth();
  const navigate = useNavigate();
  const [phase, setPhase] = useState("form"); // form | analyzing | suggestions | done | error
  const [error, setError] = useState("");
  const [answers, setAnswers] = useState({});
  const [suggestions, setSuggestions] = useState([]);
  const [selectedRoles, setSelectedRoles] = useState([]);

  useEffect(() => {
    if (user?.onboarding_complete) {
      navigate("/dashboard");
    }
  }, []);

  const runOnboarding = async (payload) => {
    try {
      setPhase("analyzing");
      const res = await api.post("/api/mentor/onboard", payload || {});
      // expect backend to return role suggestions: { roles: [...] }
      const roles = res.data?.roles || [];
      setSuggestions(roles);
      setPhase("suggestions");
    } catch (err) {
      setError(err.response?.data?.detail || "Something went wrong. Please try again.");
      setPhase("error");
    }
  };

  const finalizeOnboarding = async (chosenRoles) => {
    try {
      setPhase("analyzing");
      await api.post("/api/mentor/onboard", { answers, chosen_roles: chosenRoles });
      setPhase("done");
      await refreshUser();
      setTimeout(() => navigate("/dashboard"), 1200);
    } catch (err) {
      setError(err.response?.data?.detail || "Something went wrong. Please try again.");
      setPhase("error");
    }
  };

  const toggleAnswer = (key, value, multiple = false) => {
    setAnswers((prev) => {
      const cur = prev[key] || [];
      if (multiple) {
        const exists = cur.includes(value);
        return { ...prev, [key]: exists ? cur.filter((v) => v !== value) : [...cur, value] };
      }
      return { ...prev, [key]: [value] };
    });
  };

  return (
    <div className="onboarding-container">
      <div className="onboarding-card">
        <div className="onboarding-logo">MC</div>

        {phase === "form" && (
          <>
            <h2>Queremos conocerte mejor</h2>
            <p>Responde brevemente (selección múltiple cuando aplique). Esto nos ayuda a personalizar tu roadmap.</p>

            <OnboardingQuestions
              answers={answers}
              toggleAnswer={toggleAnswer}
              onNext={() => runOnboarding({ answers })}
              loading={phase === "analyzing"}
              nextLabel="Generar recomendaciones"
              showHeader={false}
            />
          </>
        )}

        {phase === "analyzing" && (
          <>
            <div className="spinner" />
            <h2>Procesando tus respuestas…</h2>
            <p>Estamos combinando tu perfil con el análisis de CV y repositorios para generar roles recomendados.</p>
            <div className="progress-steps">
              <div className="progress-step active">Reading CV</div>
              <div className="progress-step active">Fetching GitHub repos</div>
              <div className="progress-step">Generating analysis</div>
              <div className="progress-step">Building your roadmap</div>
            </div>
          </>
        )}

        {phase === "suggestions" && (
          <>
            <h2>Sugerencias de rol</h2>
            <p>El modelo seleccionó las mejores opciones para tu roadmap. Elige una o varias.</p>
            <div className="suggestions">
              {(suggestions.length ? suggestions : ['Software Engineer','Technical Lead','Product Engineer','Data Engineer','Full Stack Developer']).slice(0,10).map((r, i) => (
                <div key={r} className={`role-card ${selectedRoles.includes(r) ? 'selected' : ''}`} onClick={() => setSelectedRoles((s) => s.includes(r) ? s.filter(x => x !== r) : [...s, r])}>
                  <div className="role-title">{r}</div>
                  <div className="role-sub">Recomendación #{i+1}</div>
                </div>
              ))}
            </div>
            <div style={{marginTop:16}}>
              <button className="btn-primary" disabled={selectedRoles.length===0} onClick={() => finalizeOnboarding(selectedRoles)}>Confirmar rol y generar roadmap</button>
              <button className="btn-secondary" style={{marginLeft:8}} onClick={() => { setSelectedRoles(suggestions.length ? suggestions.slice(0,20) : []); finalizeOnboarding(suggestions); }}>Mostrar todas las carreras</button>
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
