import { useState, useEffect, useRef, useCallback } from "react";
import Editor from "@monaco-editor/react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import api from "../api/client";
import "./Practice.css";

const DIFFICULTIES = ["Easy", "Medium", "Hard"];
const LANGUAGES = ["python", "javascript"];
const DIFF_COLOR = { Easy: "#22c55e", Medium: "#f59e0b", Hard: "#ef4444" };

const MIN_OUTPUT_HEIGHT = 80;
const MAX_OUTPUT_HEIGHT = 600;

export default function Practice() {
  const [exercise, setExercise] = useState(null);
  const [code, setCode] = useState("");
  const [output, setOutput] = useState("");
  const [feedback, setFeedback] = useState("");
  const [history, setHistory] = useState([]);
  const [language, setLanguage] = useState("python");
  const [difficulty, setDifficulty] = useState("Easy");
  const [loadingExercise, setLoadingExercise] = useState(false);
  const [running, setRunning] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [activePanel, setActivePanel] = useState("output"); // output | feedback
  const [showHistory, setShowHistory] = useState(false);
  const [outputHeight, setOutputHeight] = useState(220);
  const dragRef = useRef(null);

  const onResizeMouseDown = useCallback((e) => {
    e.preventDefault();
    dragRef.current = { startY: e.clientY, startHeight: outputHeight };

    const onMouseMove = (e) => {
      const delta = dragRef.current.startY - e.clientY;
      const newHeight = Math.min(MAX_OUTPUT_HEIGHT, Math.max(MIN_OUTPUT_HEIGHT, dragRef.current.startHeight + delta));
      setOutputHeight(newHeight);
    };

    const onMouseUp = () => {
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
    };

    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
  }, [outputHeight]);

  useEffect(() => { loadHistory(); }, []);

  const loadHistory = async () => {
    try {
      const res = await api.get("/api/exercises/history");
      setHistory(res.data);
    } catch { }
  };

  const generateExercise = async () => {
    setLoadingExercise(true);
    setOutput("");
    setFeedback("");
    setExercise(null);
    try {
      const res = await api.post("/api/exercises/generate", { language, difficulty });
      setExercise(res.data);
      setCode(res.data.user_code || res.data.starter_code);
      setActivePanel("output");
      loadHistory();
    } catch (err) {
      setOutput("Failed to generate exercise: " + (err.response?.data?.detail || err.message));
    } finally {
      setLoadingExercise(false);
    }
  };

  const loadExercise = async (id) => {
    try {
      const res = await api.get(`/api/exercises/${id}`);
      setExercise(res.data);
      setCode(res.data.user_code || res.data.starter_code);
      setOutput(res.data.last_output || "");
      setFeedback(res.data.feedback || "");
      setShowHistory(false);
      setActivePanel(res.data.feedback ? "feedback" : "output");
    } catch { }
  };

  const runCode = async () => {
    if (!exercise) return;
    setRunning(true);
    setActivePanel("output");
    try {
      const res = await api.post("/api/exercises/run", {
        exercise_id: exercise.id,
        code,
      });
      setOutput(res.data.output);
    } catch (err) {
      setOutput("Error: " + (err.response?.data?.detail || err.message));
    } finally {
      setRunning(false);
    }
  };

  const submitCode = async () => {
    if (!exercise) return;
    setSubmitting(true);
    try {
      const res = await api.post("/api/exercises/submit", {
        exercise_id: exercise.id,
        code,
      });
      setOutput(res.data.output);
      setFeedback(res.data.feedback);
      setExercise((e) => ({ ...e, solved: res.data.success }));
      setActivePanel("feedback");
      loadHistory();
    } catch (err) {
      setOutput("Error: " + (err.response?.data?.detail || err.message));
    } finally {
      setSubmitting(false);
    }
  };

  const examples = (() => {
    try { return JSON.parse(exercise?.examples || "[]"); } catch { return []; }
  })();

  return (
    <div className="practice-layout">
      {/* Left panel: problem */}
      <div className="problem-panel">
        <div className="problem-toolbar">
          <div className="toolbar-controls">
            <select value={language} onChange={(e) => setLanguage(e.target.value)} className="select">
              {LANGUAGES.map((l) => <option key={l} value={l}>{l}</option>)}
            </select>
            <select value={difficulty} onChange={(e) => setDifficulty(e.target.value)} className="select">
              {DIFFICULTIES.map((d) => <option key={d} value={d}>{d}</option>)}
            </select>
            <button className="btn-generate" onClick={generateExercise} disabled={loadingExercise}>
              {loadingExercise ? "Generating..." : "New Exercise"}
            </button>
          </div>
          <button className="btn-history" onClick={() => setShowHistory((s) => !s)}>
            History ({history.length})
          </button>
        </div>

        {/* History dropdown */}
        {showHistory && (
          <div className="history-list">
            {history.length === 0 && <p className="no-history">No exercises yet</p>}
            {history.map((h) => (
              <button key={h.id} className="history-item" onClick={() => loadExercise(h.id)}>
                <span className="history-title">{h.title}</span>
                <div className="history-meta">
                  <span style={{ color: DIFF_COLOR[h.difficulty] }}>{h.difficulty}</span>
                  <span className="history-lang">{h.language}</span>
                  {h.solved && <span className="solved-badge">✓</span>}
                </div>
              </button>
            ))}
          </div>
        )}

        {/* Problem description */}
        <div className="problem-content">
          {!exercise && !loadingExercise && (
            <div className="empty-state">
              <div className="empty-icon">💡</div>
              <h3>Ready to practice?</h3>
              <p>Select a language and difficulty, then click <strong>New Exercise</strong> to get a coding challenge tailored to your level.</p>
            </div>
          )}

          {loadingExercise && (
            <div className="empty-state">
              <div className="spinner-sm" />
              <p>Your mentor is crafting your exercise...</p>
            </div>
          )}

          {exercise && !loadingExercise && (
            <>
              <div className="problem-header">
                <h2>{exercise.title}</h2>
                <div className="problem-tags">
                  <span className="diff-badge" style={{ background: DIFF_COLOR[exercise.difficulty] + "22", color: DIFF_COLOR[exercise.difficulty] }}>
                    {exercise.difficulty}
                  </span>
                  <span className="topic-badge">{exercise.topic || exercise.language}</span>
                  {exercise.solved && <span className="solved-badge-lg">✓ Solved</span>}
                </div>
              </div>

              <div className="problem-body">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{exercise.description}</ReactMarkdown>
              </div>

              {examples.length > 0 && (
                <div className="examples">
                  <h4>Examples</h4>
                  {examples.map((ex, i) => (
                    <div key={i} className="example-block">
                      <div><strong>Input:</strong> <code>{ex.input}</code></div>
                      <div><strong>Output:</strong> <code>{ex.output}</code></div>
                      {ex.explanation && <div className="example-explanation">{ex.explanation}</div>}
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Right panel: editor + output */}
      <div className="editor-panel">
        {/* Editor */}
        <div className="editor-wrapper">
          <div className="editor-header">
            <span className="editor-lang-label">{language}</span>
            <div className="editor-actions">
              <button className="btn-run" onClick={runCode} disabled={running || !exercise}>
                {running ? "Running..." : "▶ Run"}
              </button>
              <button className="btn-submit" onClick={submitCode} disabled={submitting || !exercise}>
                {submitting ? "Evaluating..." : "Submit & Get Feedback"}
              </button>
            </div>
          </div>
          <Editor
            height="100%"
            language={language === "javascript" ? "javascript" : "python"}
            value={code}
            onChange={(val) => setCode(val || "")}
            theme="vs-dark"
            options={{
              fontSize: 14,
              minimap: { enabled: false },
              scrollBeyondLastLine: false,
              lineNumbers: "on",
              automaticLayout: true,
              tabSize: language === "python" ? 4 : 2,
              padding: { top: 12 },
            }}
          />
        </div>

        {/* Output / Feedback */}
        <div className="output-panel" style={{ height: outputHeight }}>
          <div className="output-resize-handle" onMouseDown={onResizeMouseDown} />
          <div className="output-tabs">
            <button
              className={`output-tab ${activePanel === "output" ? "active" : ""}`}
              onClick={() => setActivePanel("output")}
            >
              Output
            </button>
            <button
              className={`output-tab ${activePanel === "feedback" ? "active" : ""} ${feedback ? "has-feedback" : ""}`}
              onClick={() => setActivePanel("feedback")}
            >
              AI Feedback {feedback && "●"}
            </button>
          </div>

          <div className="output-content">
            {activePanel === "output" && (
              <pre className="output-pre">
                {output || (exercise ? "Click ▶ Run to execute your code" : "Generate an exercise to start")}
              </pre>
            )}
            {activePanel === "feedback" && (
              <div className="feedback-content">
                {feedback
                  ? <ReactMarkdown remarkPlugins={[remarkGfm]}>{feedback}</ReactMarkdown>
                  : <p className="no-feedback">Submit your solution to get your mentor's feedback.</p>
                }
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
