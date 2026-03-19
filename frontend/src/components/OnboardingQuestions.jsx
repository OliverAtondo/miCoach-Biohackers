import React from "react";

const QUESTION_SETS = [
  {
    key: "responsibilities",
    label: "1. ¿Cuáles son tus responsabilidades principales?",
    options: ["Desarrollo", "Gestión de equipo", "Diseño", "Producto", "Ventas", "Investigación"],
  },
  {
    key: "metrics",
    label: "2. ¿Qué métricas indican tu éxito? (elige hasta 3)",
    options: ["Entrega a tiempo", "Calidad de código", "Crecimiento de usuarios", "Satisfacción cliente", "Ingresos", "Promociones"],
  },
  {
    key: "problems",
    label: "3. ¿Qué problemas interfieren con tu éxito?",
    options: ["Falta de tiempo", "Falta de mentor", "Brechas de habilidades", "Política interna", "Objetivos poco claros", "Recursos limitados"],
  },
  {
    key: "approach",
    label: "4. ¿Cómo abordas tu desarrollo de carrera actualmente?",
    options: ["Autoestudio", "Cursos formales", "Mentoría", "On-the-job", "Conferencias", "Nada"],
  },
  {
    key: "gaps",
    label: "5. ¿Qué brechas de habilidades identificas?",
    options: ["Arquitectura", "Testing", "Liderazgo", "Comunicación", "Data", "Cloud"],
  },
  {
    key: "aspiration",
    label: "6. ¿Cuáles son tus aspiraciones y plazo?",
    options: ["Senior (6-12m)", "Líder (1-2a)", "Cambio de carrera (1-2a)", "Fundador (3+a)", "Especialista (6-12m)"],
  },
  {
    key: "learning",
    label: "7. ¿Cómo prefieres aprender?",
    options: ["Videos", "Proyectos prácticos", "Mentoría", "Lectura", "Bootcamp", "Workshops"],
  },
];

export default function OnboardingQuestions({
  answers,
  toggleAnswer,
  onBack,
  onNext,
  loading,
  backLabel = "\u2190 Back",
  nextLabel = "Next →",
  showHeader = true,
}) {
  return (
    <div className="auth-form">
      {showHeader && (
        <>
          <h2>Cuestionario breve</h2>
          <p>Selecciona las opciones que aplican. Esto nos ayudará a recomendar roles y un roadmap.</p>
        </>
      )}

      {QUESTION_SETS.map((q) => (
        <div key={q.key} className="question">
          <label>{q.label}</label>
          <div className="options">
            {q.options.map((o) => (
              <button
                key={o}
                type="button"
                className={`option-btn ${answers[q.key]?.includes(o) ? "active" : ""}`}
                onClick={() => toggleAnswer(q.key, o, true)}
              >
                {o}
              </button>
            ))}
          </div>
        </div>
      ))}

      <div className="step-buttons">
        {onBack && (
          <button type="button" className="btn-secondary" onClick={onBack}>
            {backLabel}
          </button>
        )}
        <button type="button" className="btn-primary" onClick={onNext} disabled={loading}>
          {loading ? "Generando sugerencias..." : nextLabel}
        </button>
      </div>
    </div>
  );
}
