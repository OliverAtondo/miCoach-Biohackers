import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";
import { useAuth } from "../contexts/AuthContext";
import Practice from "./Practice";
import Interview from "./Interview";
import api from "../api/client";
import "./Dashboard.css";

const NAV_ITEMS = [
  { id: "Chat",      icon: "💬", label: "Chat" },
  { id: "Roadmap",   icon: "🗺",  label: "Roadmap" },
  { id: "Analysis",  icon: "📊", label: "Analysis" },
  { id: "Practice",  icon: "⚡", label: "Practice" },
  { id: "Interview", icon: "🎙", label: "Interview" }
];

export default function Dashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [view, setView] = useState("Home");
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const messagesEndRef = useRef(null);

  // Roadmap progress state
  const [roadmapUnits, setRoadmapUnits] = useState([]);
  const [roadmapLoading, setRoadmapLoading] = useState(false);
  const [roadmapError, setRoadmapError] = useState("");
  const [expandedUnit, setExpandedUnit] = useState(null);
  const [githubInputs, setGithubInputs] = useState({});
  const [submitting, setSubmitting] = useState({});
  const [evalResults, setEvalResults] = useState({});
  

  // Hot Topics state
  const [hotTopics, setHotTopics] = useState([]);
  const [topicsLoading, setTopicsLoading] = useState(true);
  const [topicsError, setTopicsError] = useState("");
  const [showAllTopics, setShowAllTopics] = useState(false);

  useEffect(() => {
    if (!user?.onboarding_complete) {
      navigate("/onboarding");
      return;
    }
    loadHistory();
    loadHotTopics();
  }, [user]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);
  

  const loadHotTopics = async () => {
    setTopicsLoading(true);
    setTopicsError("");
    try {
      // Enviar el rol del usuario para filtrar noticias relevantes
      const res = await api.get("/api/hot-topics/relevant", {
        params: { role: user?.career_path || "" }
      });
      setHotTopics(res.data.results || res.data || []);
    } catch (err) {
      setTopicsError("Could not load topics.");
    } finally {
      setTopicsLoading(false);
    }
  };

  const loadHistory = async () => {
    try {
      const res = await api.get("/api/mentor/chat/history");
      if (res.data.length === 0) {
        setMessages([{
          id: 0,
          role: "model",
          content: `Hi ${user?.name}! 👋 I'm your personal tech mentor. I've analyzed your profile and built a custom roadmap for you.

You can ask me anything — about your learning path, specific technologies, how to approach projects, or career advice. I'm here to help you become a **${user?.career_path}**!

What would you like to explore first?`,
          created_at: new Date().toISOString(),
        }]);
      } else {
        setMessages(res.data);
      }
    } catch { /* ignore */ }
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || sending) return;
    const userMsg = { id: Date.now(), role: "user", content: input, created_at: new Date().toISOString() };
    setMessages((m) => [...m, userMsg]);
    setInput("");
    setSending(true);
    try {
      const res = await api.post("/api/mentor/chat", { content: userMsg.content });
      setMessages((m) => [...m, res.data]);
    } catch {
      setMessages((m) => [...m, {
        id: Date.now() + 1, role: "model",
        content: "Sorry, I had trouble responding. Please try again.",
        created_at: new Date().toISOString(),
      }]);
    } finally {
      setSending(false);
    }
  };

  const handleLogout = () => { logout(); navigate("/login"); };

  const initializeRoadmap = async () => {
    setRoadmapLoading(true);
    setRoadmapError("");
    try {
      const res = await api.post("/api/roadmap/initialize");
      setRoadmapUnits(res.data);
      const inProgress = res.data.find((u) => u.status === "in_progress");
      if (inProgress) setExpandedUnit(inProgress.id);
    } catch (e) {
      setRoadmapError(e?.response?.data?.detail || "Failed to initialize roadmap units.");
    } finally {
      setRoadmapLoading(false);
    }
  };

  const submitGithub = async (unitId) => {
    const link = githubInputs[unitId]?.trim();
    if (!link) return;
    setSubmitting((s) => ({ ...s, [unitId]: true }));
    setEvalResults((r) => ({ ...r, [unitId]: null }));
    try {
      const res = await api.post(`/api/roadmap/units/${unitId}/submit`, { github_link: link });
      setEvalResults((r) => ({ ...r, [unitId]: res.data }));
      // Reload units to reflect status changes
      const updated = await api.get("/api/roadmap/units");
      setRoadmapUnits(updated.data);
      const inProgress = updated.data.find((u) => u.status === "in_progress" && u.id !== unitId);
      if (inProgress) setExpandedUnit(inProgress.id);
    } catch (e) {
      setEvalResults((r) => ({ ...r, [unitId]: { error: e?.response?.data?.detail || "Submission failed." } }));
    } finally {
      setSubmitting((s) => ({ ...s, [unitId]: false }));
    }
  };

  const [roadmapOpen, setRoadmapOpen] = useState(false);

  useEffect(() => {
    if (view !== "Roadmap") return;
    if (roadmapUnits.length > 0) return;
    // Try loading existing units first; if none, auto-initialize
    (async () => {
      try {
        const res = await api.get("/api/roadmap/units");
        if (res.data.length > 0) {
          setRoadmapUnits(res.data);
          const inProgress = res.data.find((u) => u.status === "in_progress");
          if (inProgress) setExpandedUnit(inProgress.id);
        } else {
          await initializeRoadmap();
        }
      } catch {
        await initializeRoadmap();
      }
    })();
  }, [view]);

  const initials = user?.name
    ? user.name.split(" ").map((n) => n[0]).slice(0, 2).join("").toUpperCase()
    : "U";

  return (
    <div className="dashboard-root">

      {/* ── Top Navbar (coach style) ── */}
      <header className="dash-navbar">
        <div className="dash-navbar-left">
          <div className="dash-menu-wrap">
            <button
              className="dash-menu-btn"
              onClick={() => setMenuOpen((o) => !o)}
              aria-label="Menu"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24"
                fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="3" y1="12" x2="21" y2="12" />
                <line x1="3" y1="6"  x2="21" y2="6"  />
                <line x1="3" y1="18" x2="21" y2="18" />
              </svg>
            </button>
            {menuOpen && (
              <div className="dash-menu-dropdown">
                <button onClick={() => { setView("Home"); setMenuOpen(false); }}>
                  🏠 Dashboard
                </button>
                <button onClick={() => { setView("Chat"); setMenuOpen(false); }}>
                  💬 Talk to my Coach
                </button>
              </div>
            )}
          </div>
          <button className="dash-navbar-logo" onClick={() => setView("Home")}>
            <span className="dash-navbar-logo-text">miCoach</span>
            <span className="dash-navbar-logo-sub">powered by AI</span>
          </button>
        </div>

        <div className="dash-navbar-right">
          <button className="dash-notif-btn" aria-label="Notifications">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"
              fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
              <path d="M13.73 21a2 2 0 0 1-3.46 0" />
            </svg>
            <span className="dash-notif-dot" />
          </button>

          <div className="dash-profile-menu" onClick={() => setProfileOpen((o) => !o)}>
            <div className="dash-profile-info">
              <span className="dash-profile-name">Hi {user?.name?.split(" ")[0]}</span>
              <span className="dash-profile-progress">{user?.career_path}</span>
            </div>
            <div className="dash-profile-avatar">{initials}</div>
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24"
              fill="none" stroke="#94a3b8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="6 9 12 15 18 9" />
            </svg>
            {profileOpen && (
              <div className="dash-profile-dropdown">
                <button onClick={handleLogout}>Sign Out</button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* ── Body: sidebar + main ── */}
      <div className="dashboard-body">

        {/* ── Sidebar (hidden on Home view) ── */}
        <aside className={`sidebar ${view === "Home" ? "sidebar-hidden" : ""}`}>
          <nav className="sidebar-nav">
            {NAV_ITEMS.map(({ id, icon, label }) => (
              <button
                key={id}
                className={`nav-item ${view === id ? "active" : ""}`}
                onClick={() => setView(id)}
              >
                <span className="nav-icon">{icon}</span>
                {label}
              </button>
            ))}
          </nav>

        </aside>

        {/* ── Main content ── */}
        <main className="main-content">

          {/* ── HOME VIEW ── */}
          {view === "Home" && (
            <div className="home-scroll">
              <div className="home-inner">
              <div className="home-page-header">
                <h2>Hi {user?.name}</h2>
                <div className="home-page-actions">
                  <button className="btn btn-outline btn-sm" onClick={() => setView("Analysis")}>View Analysis</button>
                  <button className="btn btn-primary btn-sm" onClick={() => setView("Roadmap")}>My Roadmap</button>
                </div>
              </div>

              <div className="home-grid">
                {/* Left col */}
                <div className="home-left">
                  <div className="card banner-card">
                    <div className="banner-content">
                      <h3>Interact with your personal AI Coach!</h3>
                      <p>Talk to your personal AI Coach, find guidance and grow your professional career.</p>
                      <button className="btn btn-primary mt-4" onClick={() => setView("Chat")}>Talk to my Coach</button>
                    </div>
                    <div className="banner-deco" />
                  </div>

                  <div className="card hot-topics-card">
                    <h4 className="card-title">Temas del Momento</h4>
                    {topicsLoading ? (
                      <div className="loading-spinner"></div>
                    ) : topicsError ? (
                      <div className="topics-error">{topicsError}</div>
                    ) : (
                      <>
                        <div className="hot-topics-list">
                          {(showAllTopics ? hotTopics : hotTopics.slice(0, 7)).map((topic, i) => (
                            <a href={topic.url} target="_blank" rel="noopener noreferrer" key={i} className="hot-topic-item">
                              <div className="hot-topic-header">
                                <span className="hot-topic-title">{topic.title}</span>
                                <span className="hot-topic-source">{topic.source}</span>
                              </div>
                              {topic.summary && (
                                <div className="hot-topic-summary">{topic.summary}</div>
                              )}
                            </a>
                          ))}
                        </div>
                        <div className="hot-topics-actions">
                          {hotTopics.length > 7 && (
                            <button className="btn btn-outline btn-sm" onClick={() => setShowAllTopics((v) => !v)}>
                              {showAllTopics ? "Ver menos" : "Ver más"}
                            </button>
                          )}
                          <button className="btn btn-primary btn-sm" style={{marginLeft:8}} onClick={loadHotTopics} disabled={topicsLoading}>
                            Refrescar
                          </button>
                        </div>
                      </>
                    )}
                  </div>

                  <div className="card achievements-card">
                    <h4 className="card-title">My achievements</h4>
                    <div className="achievements-list">
                      <div className="achievement-item">
                        <div className="achievement-icon icon-blue">
                          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#2563eb" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <circle cx="12" cy="8" r="7" /><polyline points="8.21 13.89 7 23 12 20 17 23 15.79 13.88" />
                          </svg>
                        </div>
                        <div className="achievement-data">
                          <span className="ach-value">76 <span className="ach-unit">pts</span></span>
                          <span className="ach-label">Points earned</span>
                        </div>
                      </div>
                      <div className="achievement-item">
                        <div className="achievement-icon icon-blue">
                          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#2563eb" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" /><polyline points="22 4 12 14.01 9 11.01" />
                          </svg>
                        </div>
                        <div className="achievement-data">
                          <span className="ach-value">02</span>
                          <span className="ach-label">Certifications</span>
                        </div>
                      </div>
                      <div className="achievement-item">
                        <div className="achievement-icon icon-teal">
                          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#0d9488" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
                          </svg>
                        </div>
                        <div className="achievement-data">
                          <span className="ach-value">34</span>
                          <span className="ach-label">Hours of training</span>
                        </div>
                      </div>
                    </div>
                  </div>

                </div>

                {/* Right col */}
                <div className="home-right">

                  <div className="card quick-actions-card">
                    <div className="action-row" onClick={() => setView("Practice")}>
                      <div className="action-icon-box">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2563eb" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <polyline points="16 18 22 12 16 6" /><polyline points="8 6 2 12 8 18" />
                        </svg>
                      </div>
                      <div className="action-text">
                        <h5>Coding Practice</h5>
                        <span>AI-generated exercises tailored to your path</span>
                      </div>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" strokeWidth="2"><polyline points="9 18 15 12 9 6" /></svg>
                    </div>
                    <div className="action-row" onClick={() => setView("Interview")}>
                      <div className="action-icon-box">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2563eb" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z" />
                          <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                          <line x1="12" y1="19" x2="12" y2="22" /><line x1="8" y1="22" x2="16" y2="22" />
                        </svg>
                      </div>
                      <div className="action-text">
                        <h5>Mock Interview</h5>
                        <span>Practice with AI-powered voice interviews</span>
                      </div>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" strokeWidth="2"><polyline points="9 18 15 12 9 6" /></svg>
                    </div>
                    <div className="action-row last" onClick={() => setView("Roadmap")}>
                      <div className="action-icon-box">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2563eb" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <polygon points="3 11 22 2 13 21 11 13 3 11" />
                        </svg>
                      </div>
                      <div className="action-text">
                        <h5>Learning Roadmap</h5>
                        <span>Your personalized path to {user?.career_path}</span>
                      </div>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" strokeWidth="2"><polyline points="9 18 15 12 9 6" /></svg>
                    </div>
                  </div>
                  <div className="card skills-card">
                    <h4 className="card-title">Skills proficiency</h4>
                    <p className="card-desc">Access the detailed report and identify improvement opportunities for your career progress.</p>
                    <div className="skills-legend">
                      <div className="legend-item"><span className="color-box self" />Self assessment</div>
                      <div className="legend-item"><span className="color-box expected" />Expected level</div>
                    </div>
                    <div className="radar-wrap">
                      <svg viewBox="0 0 200 200" className="radar-svg">
                        <polygon points="100,20 170,60 170,140 100,180 30,140 30,60" fill="none" stroke="#e2e8f0" strokeWidth="1" />
                        <polygon points="100,40 152,70 152,130 100,160 48,130 48,70" fill="none" stroke="#e2e8f0" strokeWidth="1" />
                        <polygon points="100,60 135,80 135,120 100,140 65,120 65,80" fill="none" stroke="#e2e8f0" strokeWidth="1" />
                        <polygon points="100,80 117,90 117,110 100,120 83,110 83,90" fill="none" stroke="#e2e8f0" strokeWidth="1" />
                        <line x1="100" y1="100" x2="100" y2="20" stroke="#e2e8f0" strokeWidth="1" />
                        <line x1="100" y1="100" x2="170" y2="60" stroke="#e2e8f0" strokeWidth="1" />
                        <line x1="100" y1="100" x2="170" y2="140" stroke="#e2e8f0" strokeWidth="1" />
                        <line x1="100" y1="100" x2="100" y2="180" stroke="#e2e8f0" strokeWidth="1" />
                        <line x1="100" y1="100" x2="30" y2="140" stroke="#e2e8f0" strokeWidth="1" />
                        <line x1="100" y1="100" x2="30" y2="60" stroke="#e2e8f0" strokeWidth="1" />
                        <polygon points="100,40 145,65 160,135 100,155 45,125 40,55" fill="#dbeafe" fillOpacity="0.6" stroke="#2563eb" strokeWidth="2" />
                        <polygon points="100,30 160,65 155,145 100,170 35,135 30,60" fill="none" stroke="#ec4899" strokeWidth="1" strokeDasharray="4" />
                      </svg>
                    </div>
                  </div>

                  <div className="card profile-card">
                    <div className="profile-card-header">
                      <div className="profile-card-avatar">{initials}</div>
                      <div>
                        <div className="profile-card-name">{user?.name}</div>
                        <div className="profile-card-role">{user?.career_path}</div>
                      </div>
                    </div>
                    <div className="profile-progress-row">
                      <span className="profile-progress-label">Profile completion</span>
                      <span className="profile-progress-pct">66%</span>
                    </div>
                    <div className="profile-progress-bar">
                      <div className="profile-progress-fill" style={{ width: "66%" }} />
                    </div>
                    <button className="btn btn-outline btn-block mt-3" onClick={() => setView("Chat")}>
                      Talk to my Coach
                    </button>
                  </div>
                </div>
              </div>
              </div>
            </div>
          )}

          {/* ── CHAT VIEW ── */}
          {view === "Chat" && (
            <div className="chat-view">
              <div className="chat-header">
                <h2>Chat with your Mentor</h2>
                <span className="online-badge">● Online</span>
              </div>
              <div className="messages">
                {messages.map((msg) => (
                  <div key={msg.id} className={`message ${msg.role === "user" ? "user-msg" : "model-msg"}`}>
                    {msg.role === "model" && <div className="msg-avatar">MC</div>}
                    <div className="msg-bubble">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                    </div>
                  </div>
                ))}
                {sending && (
                  <div className="message model-msg">
                    <div className="msg-avatar">MC</div>
                    <div className="msg-bubble typing"><span /><span /><span /></div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
              <form className="chat-input-form" onSubmit={sendMessage}>
                <input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Ask your mentor anything..."
                  disabled={sending}
                />
                <button type="submit" disabled={sending || !input.trim()}>Send</button>
              </form>
            </div>
          )}

          {view === "Roadmap" && (
            <div className="content-view roadmap-progress-view">
              <div className="roadmap-header">
                <div>
                  <h2>Learning Roadmap</h2>
                  <p className="roadmap-subtitle">Complete each phase project to unlock the next level</p>
                </div>
              </div>

              {/* Collapsible original roadmap */}
              <div className="roadmap-original-wrap">
                <button className="roadmap-original-toggle" onClick={() => setRoadmapOpen((o) => !o)}>
                  <span>Full roadmap details</span>
                  <span className="roadmap-unit-chevron">{roadmapOpen ? "▲" : "▼"}</span>
                </button>
                {roadmapOpen && (
                  <div className="roadmap-original-body markdown-content">
                    <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw]}>{user?.roadmap || "Roadmap not available."}</ReactMarkdown>
                  </div>
                )}
              </div>

              {roadmapError && <div className="roadmap-error">{roadmapError}</div>}

              {roadmapLoading && (
                <div className="roadmap-loading">
                  <div className="typing"><span /><span /><span /></div>
                  <p>Generating phase units from your roadmap...</p>
                </div>
              )}

              {roadmapUnits.length > 0 && (
                <div className="roadmap-units">
                  {/* Progress bar */}
                  <div className="roadmap-progress-bar-wrap">
                    <div className="roadmap-progress-label">
                      {roadmapUnits.filter((u) => u.status === "completed").length} / {roadmapUnits.length} phases completed
                    </div>
                    <div className="roadmap-progress-track">
                      <div
                        className="roadmap-progress-fill"
                        style={{ width: `${(roadmapUnits.filter((u) => u.status === "completed").length / roadmapUnits.length) * 100}%` }}
                      />
                    </div>
                  </div>

                  {roadmapUnits.map((unit, idx) => {
                    const isExpanded = expandedUnit === unit.id;
                    const evalResult = evalResults[unit.id];
                    const isSubmitting = submitting[unit.id];

                    return (
                      <div
                        key={unit.id}
                        className={`roadmap-unit-card status-${unit.status}`}
                      >
                        {/* Unit header */}
                        <button
                          className="roadmap-unit-header"
                          onClick={() => setExpandedUnit(isExpanded ? null : unit.id)}
                          disabled={unit.status === "locked"}
                        >
                          <div className="roadmap-unit-badge">
                            {unit.status === "completed" && (
                              <span className="unit-icon unit-done">✓</span>
                            )}
                            {unit.status === "in_progress" && (
                              <span className="unit-icon unit-active">{idx + 1}</span>
                            )}
                            {unit.status === "locked" && (
                              <span className="unit-icon unit-locked">🔒</span>
                            )}
                          </div>
                          <div className="roadmap-unit-meta">
                            <span className="roadmap-unit-title">{unit.title}</span>
                            <span className={`roadmap-unit-status status-label-${unit.status}`}>
                              {unit.status === "completed" ? "Completed" : unit.status === "in_progress" ? "In Progress" : "Locked"}
                            </span>
                          </div>
                          {unit.status !== "locked" && (
                            <span className="roadmap-unit-chevron">{isExpanded ? "▲" : "▼"}</span>
                          )}
                        </button>

                        {/* Expanded body */}
                        {isExpanded && unit.status !== "locked" && (
                          <div className="roadmap-unit-body">
                            <div className="roadmap-section">
                              <h4>What you'll learn</h4>
                              <p>{unit.description}</p>
                            </div>

                            <div className="roadmap-section roadmap-project-box">
                              <h4>Project to complete</h4>
                              <p>{unit.project_description}</p>
                            </div>

                            {/* GitHub submission */}
                            {unit.status === "in_progress" && (
                              <div className="roadmap-section roadmap-submit-box">
                                <h4>Submit your project</h4>
                                <p className="roadmap-submit-hint">
                                  Push your project to GitHub and paste the repository URL below.
                                  The AI will review your code and evaluate whether you're ready to advance.
                                </p>
                                <div className="roadmap-input-row">
                                  <input
                                    type="url"
                                    placeholder="https://github.com/username/repo"
                                    value={githubInputs[unit.id] || ""}
                                    onChange={(e) => setGithubInputs((g) => ({ ...g, [unit.id]: e.target.value }))}
                                    disabled={isSubmitting}
                                    className="roadmap-github-input"
                                  />
                                  <button
                                    className="btn btn-primary"
                                    onClick={() => submitGithub(unit.id)}
                                    disabled={isSubmitting || !githubInputs[unit.id]?.trim()}
                                  >
                                    {isSubmitting ? "Evaluating..." : "Submit"}
                                  </button>
                                </div>
                              </div>
                            )}

                            {/* Previous submission link */}
                            {unit.github_link && unit.status === "completed" && (
                              <div className="roadmap-section">
                                <span className="roadmap-repo-link">
                                  Submitted: <a href={unit.github_link} target="_blank" rel="noopener noreferrer">{unit.github_link}</a>
                                </span>
                              </div>
                            )}

                            {/* Evaluation result */}
                            {evalResult && !evalResult.error && (
                              <div className={`roadmap-eval-result ${evalResult.passed ? "eval-passed" : "eval-failed"}`}>
                                <div className="eval-result-header">
                                  <span className="eval-icon">{evalResult.passed ? "✓ Passed" : "✗ Not yet"}</span>
                                  <span className="eval-score">{evalResult.score}</span>
                                </div>
                                <div className="markdown-content eval-feedback">
                                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{evalResult.feedback}</ReactMarkdown>
                                </div>
                              </div>
                            )}
                            {evalResult?.error && (
                              <div className="roadmap-error">{evalResult.error}</div>
                            )}

                            {/* Previous feedback (persisted) */}
                            {unit.evaluation_feedback && !evalResult && (
                              <div className={`roadmap-eval-result ${unit.evaluation_passed ? "eval-passed" : "eval-failed"}`}>
                                <div className="eval-result-header">
                                  <span className="eval-icon">{unit.evaluation_passed ? "✓ Passed" : "✗ Not yet"}</span>
                                </div>
                                <div className="markdown-content eval-feedback">
                                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{unit.evaluation_feedback}</ReactMarkdown>
                                </div>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {view === "Analysis" && (
            <div className="content-view">
              <h2>Profile Analysis</h2>
              <div className="markdown-content">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{user?.analysis || "Analysis not available."}</ReactMarkdown>
              </div>
            </div>
          )}

          {view === "Practice" && <Practice />}
          {view === "Interview" && <Interview />}
        </main>
      </div>
    </div>
  );
}
