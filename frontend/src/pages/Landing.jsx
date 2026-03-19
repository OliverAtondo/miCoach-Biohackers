import { Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import "./Landing.css";

export default function Landing() {
  const { user } = useAuth();

  return (
    <div className="landing">
      {/* ── Header ── */}
      <header className="lnd-header">
        <div className="lnd-header-inner">
          <div className="lnd-logo">
            <span className="lnd-logo-text">miCoach</span>
            <span className="lnd-logo-sub">powered by AI</span>
          </div>
          <div className="lnd-auth-btns">
            {user ? (
              <Link to="/dashboard" className="btn btn-primary">Go to Dashboard</Link>
            ) : (
              <>
                <Link to="/login" className="btn btn-outline">Log In</Link>
                <Link to="/register" className="btn btn-primary">Sign Up</Link>
              </>
            )}
          </div>
        </div>
      </header>

      {/* ── Hero ── */}
      <section className="lnd-hero">
        <div className="lnd-hero-overlay" />
        <div className="lnd-hero-inner">
          <div className="lnd-hero-content">
            <h1>Your personal AI Career Coach for IT professionals</h1>
            <p>
              Accelerate your tech career with AI-powered mentoring, personalized learning roadmaps,
              coding practice, and mock interview preparation — all in one place.
            </p>
            <div className="lnd-hero-btns">
              <Link to="/register" className="btn btn-primary btn-lg">Get Started Free</Link>
              <Link to="/login" className="btn btn-outline-white btn-lg">Sign In</Link>
            </div>
          </div>

          <div className="lnd-hero-features" id="features">
            <ul>
              <li>AI-analyzed CV and GitHub profile to understand your skills</li>
              <li>Personalized learning roadmap based on your career goals</li>
              <li>Chat with your AI mentor anytime, about anything</li>
              <li>Coding exercises generated for your exact skill level</li>
            </ul>
          </div>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="lnd-footer">
        <div className="lnd-footer-inner">
          <span className="lnd-logo-text">miCoach</span>
          <span className="lnd-footer-copy">© {new Date().getFullYear()} miCoach. AI-powered career coaching.</span>
        </div>
      </footer>
    </div>
  );
}
