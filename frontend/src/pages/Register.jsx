import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import api from "../api/client";
import { useAuth } from "../contexts/AuthContext";
import "./Auth.css";
import "./Register.css";

const CAREER_PATHS = [
  "Frontend Developer",
  "Backend Developer",
  "Full Stack Developer",
  "DevOps / Cloud Engineer",
  "Data Scientist",
  "Machine Learning Engineer",
  "Mobile Developer (iOS/Android)",
  "Cybersecurity Engineer",
  "Blockchain Developer",
  "QA / Test Engineer",
];

const STEPS = ["Account", "Career", "Documents"];

export default function Register() {
  const navigate = useNavigate();
  const { refreshUser } = useAuth();
  const [step, setStep] = useState(0);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
    career_path: "",
    github_links: [""],
    cv: null,
  });

  const updateField = (field, value) => setForm((f) => ({ ...f, [field]: value }));

  const updateGithubLink = (i, value) => {
    const links = [...form.github_links];
    links[i] = value;
    updateField("github_links", links);
  };

  const addLink = () => updateField("github_links", [...form.github_links, ""]);
  const removeLink = (i) =>
    updateField("github_links", form.github_links.filter((_, idx) => idx !== i));

  const nextStep = (e) => {
    e.preventDefault();
    setError("");
    if (step === 0) {
      if (!form.name || !form.email || !form.password || !form.confirmPassword) return setError("Please fill all fields");
      if (form.password.length < 6) return setError("Password must be at least 6 characters");
      if (form.password !== form.confirmPassword) return setError("Passwords do not match");
    }
    if (step === 1 && !form.career_path) return setError("Please select a career path");
    setStep((s) => s + 1);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.cv) return setError("Please upload your CV in PDF format");
    setError("");
    setLoading(true);

    const data = new FormData();
    data.append("name", form.name);
    data.append("email", form.email);
    data.append("password", form.password);
    data.append("career_path", form.career_path);
    data.append("github_links", JSON.stringify(form.github_links.filter((l) => l.trim())));
    data.append("cv", form.cv);

    try {
      const res = await api.post("/api/auth/register", data);
      localStorage.setItem("token", res.data.access_token);
      await refreshUser();
      await api.post("/api/mentor/onboard");
    } catch (err) {
      setError(err.response?.data?.detail || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card register-card">
        <div className="auth-header">
          <div className="auth-logo">MC</div>
          <h1>Create your account</h1>
          <p>Let&apos;s set up your personalized mentor</p>
        </div>

        {/* Step indicator */}
        <div className="steps">
          {STEPS.map((s, i) => (
            <div key={s} className={`step ${i === step ? "active" : i < step ? "done" : ""}`}>
              <div className="step-dot">{i < step ? "✓" : i + 1}</div>
              <span>{s}</span>
            </div>
          ))}
        </div>

        {error && <div className="error-box">{error}</div>}

        {/* Step 0: Account */}
        {step === 0 && (
          <form onSubmit={nextStep} className="auth-form">
            <div className="field">
              <label>Full Name</label>
              <input
                value={form.name}
                onChange={(e) => updateField("name", e.target.value)}
                placeholder="Jane Doe"
                required
              />
            </div>
            <div className="field">
              <label>Email</label>
              <input
                type="email"
                value={form.email}
                onChange={(e) => updateField("email", e.target.value)}
                placeholder="you@example.com"
                required
              />
            </div>
            <div className="field">
              <label>Password</label>
              <input
                type="password"
                value={form.password}
                onChange={(e) => updateField("password", e.target.value)}
                placeholder="Min 6 characters"
                required
              />
            </div>
            <div className="field">
              <label>Confirm Password</label>
              <input
                type="password"
                value={form.confirmPassword}
                onChange={(e) => updateField("confirmPassword", e.target.value)}
                placeholder="Repeat your password"
                required
              />
            </div>
            <button type="submit" className="btn-primary">Next &rarr;</button>
          </form>
        )}

        {/* Step 1: Career */}
        {step === 1 && (
          <form onSubmit={nextStep} className="auth-form">
            <div className="field">
              <label>Career Path</label>
              <p className="field-hint">What role do you want to grow into?</p>
              <div className="career-grid">
                {CAREER_PATHS.map((path) => (
                  <button
                    key={path}
                    type="button"
                    className={`career-chip ${form.career_path === path ? "selected" : ""}`}
                    onClick={() => updateField("career_path", path)}
                  >
                    {path}
                  </button>
                ))}
              </div>
            </div>
            <div className="step-buttons">
              <button type="button" className="btn-secondary" onClick={() => setStep(0)}>&larr; Back</button>
              <button type="submit" className="btn-primary">Next &rarr;</button>
            </div>
          </form>
        )}

        {/* Step 2: Documents */}
        {step === 2 && (
          <form onSubmit={handleSubmit} className="auth-form">
            <div className="field">
              <label>Upload CV (PDF)</label>
              <div
                className={`file-drop ${form.cv ? "has-file" : ""}`}
                onClick={() => document.getElementById("cv-input").click()}
              >
                {form.cv ? (
                  <div className="file-info">
                    <span className="file-icon">📄</span>
                    <span>{form.cv.name}</span>
                    <button
                      type="button"
                      className="remove-file"
                      onClick={(e) => { e.stopPropagation(); updateField("cv", null); }}
                    >✕</button>
                  </div>
                ) : (
                  <>
                    <span className="upload-icon">⬆</span>
                    <span>Click to upload PDF</span>
                    <span className="upload-hint">Max 10MB</span>
                  </>
                )}
              </div>
              <input
                id="cv-input"
                type="file"
                accept=".pdf"
                style={{ display: "none" }}
                onChange={(e) => updateField("cv", e.target.files[0])}
              />
            </div>

            <div className="field">
              <label>GitHub Projects</label>
              <p className="field-hint">Add links to relevant repositories</p>
              {form.github_links.map((link, i) => (
                <div key={i} className="link-row">
                  <input
                    type="url"
                    value={link}
                    onChange={(e) => updateGithubLink(i, e.target.value)}
                    placeholder="https://github.com/user/repo"
                  />
                  {form.github_links.length > 1 && (
                    <button type="button" className="remove-link" onClick={() => removeLink(i)}>✕</button>
                  )}
                </div>
              ))}
              <button type="button" className="btn-add-link" onClick={addLink}>+ Add another repo</button>
            </div>

            <div className="step-buttons">
              <button type="button" className="btn-secondary" onClick={() => setStep(1)}>&larr; Back</button>
              <button type="submit" className="btn-primary" disabled={loading}>
                {loading ? "Creating account..." : "Create Account"}
              </button>
            </div>
          </form>
        )}

        <p className="auth-footer">
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  );
}
