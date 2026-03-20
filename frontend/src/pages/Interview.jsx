import { useState, useEffect, useRef, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useAuth } from "../contexts/AuthContext";
import api from "../api/client";
import { textToSpeech } from "../utils/elevenlabs";
import "./Interview.css";

const TOTAL = 5;

const SpeechRecognitionAPI = window.SpeechRecognition || window.webkitSpeechRecognition;

export default function Interview() {
  const { user } = useAuth();

  // phase: idle | loading | speaking | listening | processing | speaking-final | finished
  const [phase, setPhase] = useState("idle");
  const [sessionId, setSessionId] = useState(null);
  const [turnNumber, setTurnNumber] = useState(1);
  const [question, setQuestion] = useState("");
  const [transcript, setTranscript] = useState("");
  const [interimTranscript, setInterimTranscript] = useState("");
  const [typedAnswer, setTypedAnswer] = useState("");
  // Default to text if browser STT not available
  const [inputMode, setInputMode] = useState(SpeechRecognitionAPI ? "voice" : "text");
  const [finalFeedback, setFinalFeedback] = useState("");
  const [score, setScore] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [selectedSession, setSelectedSession] = useState(null);
  const [loadingSession, setLoadingSession] = useState(false);
  const [error, setError] = useState("");

  const recognitionRef = useRef(null);
  const audioSourceRef = useRef(null); // AudioBufferSourceNode
  const audioCtxRef = useRef(null);    // AudioContext (unlocked on user gesture)

  useEffect(() => { loadSessions(); }, []);

  // Stop audio on unmount
  useEffect(() => {
    return () => {
      stopAudio();
      if (recognitionRef.current) recognitionRef.current.abort();
      if (audioCtxRef.current) { audioCtxRef.current.close(); audioCtxRef.current = null; }
    };
  }, []);

  const unlockAudio = () => {
    if (!audioCtxRef.current) {
      audioCtxRef.current = new AudioContext();
    } else if (audioCtxRef.current.state === "suspended") {
      audioCtxRef.current.resume();
    }
  };

  const stopAudio = () => {
    if (audioSourceRef.current) {
      try { audioSourceRef.current.stop(); } catch {}
      audioSourceRef.current = null;
    }
  };

  const loadSessions = async () => {
    try {
      const res = await api.get("/api/interview/sessions");
      setSessions(res.data);
    } catch { }
  };

  const openSession = async (id) => {
    setLoadingSession(true);
    setSelectedSession(null);
    try {
      const res = await api.get(`/api/interview/sessions/${id}`);
      setSelectedSession(res.data);
    } catch { }
    finally { setLoadingSession(false); }
  };

  const speak = useCallback(async (text, onEnd) => {
    stopAudio();
    const ctx = audioCtxRef.current;
    if (!ctx) { if (onEnd) onEnd(); return; }
    try {
      const blob = await textToSpeech(text);
      const arrayBuffer = await blob.arrayBuffer();
      const audioBuffer = await ctx.decodeAudioData(arrayBuffer);
      const source = ctx.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(ctx.destination);
      audioSourceRef.current = source;
      source.onended = () => {
        audioSourceRef.current = null;
        if (onEnd) onEnd();
      };
      source.start();
    } catch (err) {
      console.error("ElevenLabs TTS error:", err);
      if (onEnd) onEnd();
    }
  }, []);

  const startListening = useCallback(() => {
    if (!SpeechRecognitionAPI) return;
    setTranscript("");
    setInterimTranscript("");
    setTypedAnswer("");
    setPhase("listening");

    const recognition = new SpeechRecognitionAPI();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "en-US";

    recognition.onresult = (event) => {
      let interim = "";
      let final = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        if (event.results[i].isFinal) {
          final += event.results[i][0].transcript + " ";
        } else {
          interim += event.results[i][0].transcript;
        }
      }
      if (final) setTranscript(prev => prev + final);
      setInterimTranscript(interim);
    };

    recognition.onerror = (e) => {
      if (e.error !== "aborted") setError("Microphone error: " + e.error);
    };

    recognitionRef.current = recognition;
    recognition.start();
  }, []);

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      recognitionRef.current = null;
    }
    setInterimTranscript("");
  }, []);

  const submitAnswer = useCallback(async (answerText) => {
    if (!answerText.trim()) {
      setError("Please provide an answer before submitting.");
      setPhase("listening");
      return;
    }

    setPhase("processing");
    setError("");
    try {
      const res = await api.post("/api/interview/respond", {
        session_id: sessionId,
        turn_number: turnNumber,
        answer: answerText.trim(),
      });

      if (res.data.is_final) {
        setFinalFeedback(res.data.feedback);
        setScore(res.data.score);
        setPhase("speaking-final");
        speak("Thank you for completing the interview. Here is your detailed feedback.", () => {
          setPhase("finished");
        });
        loadSessions();
      } else {
        setQuestion(res.data.question);
        setTurnNumber(res.data.turn);
        setTranscript("");
        setTypedAnswer("");
        setPhase("speaking");
        speak(res.data.question, () => {
          setPhase("listening");
          if (inputMode === "voice") startListening();
        });
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Error submitting answer.");
      setPhase("listening");
    }
  }, [sessionId, turnNumber, speak, startListening, inputMode]);

  const handleStopAndSubmit = useCallback(() => {
    stopListening();
    submitAnswer(transcript + interimTranscript);
  }, [stopListening, transcript, interimTranscript, submitAnswer]);

  const handleTextSubmit = useCallback(() => {
    submitAnswer(typedAnswer);
  }, [typedAnswer, submitAnswer]);

  const startInterview = async () => {
    unlockAudio(); // must be before any await — user gesture context
    setError("");
    setSelectedSession(null);
    setPhase("loading");
    setTranscript("");
    setTypedAnswer("");
    setFinalFeedback("");
    setScore(null);

    try {
      const res = await api.post("/api/interview/start");
      setSessionId(res.data.session_id);
      setTurnNumber(res.data.turn);
      setQuestion(res.data.question);
      setPhase("speaking");
      speak(res.data.question, () => {
        setPhase("listening");
        if (inputMode === "voice") startListening();
      });
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to start interview.");
      setPhase("idle");
    }
  };

  const resetInterview = () => {
    stopAudio();
    if (audioCtxRef.current) { audioCtxRef.current.close(); audioCtxRef.current = null; }
    if (recognitionRef.current) { recognitionRef.current.abort(); recognitionRef.current = null; }
    setPhase("idle");
    setSessionId(null);
    setQuestion("");
    setTranscript("");
    setInterimTranscript("");
    setTypedAnswer("");
    setFinalFeedback("");
    setScore(null);
    setError("");
  };

  // ── Render ──────────────────────────────────────────────────────────────

  // Session detail view
  if (phase === "idle" && selectedSession) {
    return (
      <div className="interview-detail">
        <div className="detail-header">
          <button className="btn-back" onClick={() => setSelectedSession(null)}>← Back</button>
          <div className="detail-meta">
            <span className="detail-date">{new Date(selectedSession.created_at).toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" })}</span>
            <span className={`session-status ${selectedSession.status}`}>{selectedSession.status === "completed" ? "Completed" : "Incomplete"}</span>
          </div>
          {selectedSession.score && <div className="final-score">{selectedSession.score}</div>}
          <button className="btn-start-interview" style={{ marginLeft: "auto" }} onClick={startInterview}>New Interview</button>
        </div>

        <div className="detail-body">
          <div className="transcript-section">
            <h3 className="section-title">Interview Transcript</h3>
            {selectedSession.turns.map((t) => (
              <div key={t.turn_number} className="turn-block">
                <div className="turn-question">
                  <span className="turn-label">Q{t.turn_number}</span>
                  <p>{t.question}</p>
                </div>
                {t.answer && (
                  <div className="turn-answer">
                    <span className="turn-label answer-label">You</span>
                    <p>{t.answer}</p>
                  </div>
                )}
              </div>
            ))}
          </div>

          {selectedSession.final_feedback && (
            <div className="feedback-section">
              <h3 className="section-title">AI Feedback</h3>
              <div className="final-feedback">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{selectedSession.final_feedback}</ReactMarkdown>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  // Idle screen
  if (phase === "idle") {
    return (
      <div className="interview-idle">
        <div className="idle-hero">
          <div className="idle-icon">🎤</div>
          <h2>Mock Interview</h2>
          <p>Practice a {TOTAL}-question technical interview for <strong>{user?.career_path}</strong>. The AI will speak each question aloud via ElevenLabs.</p>
          <button className="btn-start-interview" onClick={startInterview}>
            Start Interview
          </button>
          {error && <p className="interview-error">{error}</p>}
        </div>

        {sessions.length > 0 && (
          <div className="past-sessions">
            <h3>Past Sessions</h3>
            {loadingSession && <p style={{ color: "#555", fontSize: "0.85rem", padding: "0.5rem 0" }}>Loading...</p>}
            <div className="sessions-list">
              {sessions.map((s) => (
                <div key={s.id} className="session-card">
                  <div className="session-info">
                    <span className={`session-status ${s.status}`}>{s.status === "completed" ? "Completed" : "Incomplete"}</span>
                    <span className="session-date">{new Date(s.created_at).toLocaleDateString()}</span>
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                    {s.score && <div className="session-score">{s.score}</div>}
                    <button className="btn-view-session" onClick={() => openSession(s.id)}>View →</button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }

  // Finished screen
  if (phase === "finished" || phase === "speaking-final") {
    return (
      <div className="interview-finished">
        <div className="finished-header">
          <h2>Interview Complete</h2>
          {score && <div className="final-score">{score}</div>}
          <button className="btn-new-interview" onClick={resetInterview}>New Interview</button>
        </div>
        <div className="final-feedback">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{finalFeedback}</ReactMarkdown>
        </div>
      </div>
    );
  }

  // Active interview
  return (
    <div className="interview-active">
      <div className="interview-progress-bar">
        <div className="progress-fill" style={{ width: `${((turnNumber - 1) / TOTAL) * 100}%` }} />
      </div>

      <div className="interview-header">
        <span className="interview-label">Mock Interview</span>
        <span className="turn-indicator">Question {turnNumber} / {TOTAL}</span>
        <button className="btn-end-interview" onClick={resetInterview}>End</button>
      </div>

      {/* AI Avatar */}
      <div className="ai-section">
        <div className={`ai-avatar ${phase === "speaking" ? "speaking" : ""}`}>
          <span>AI</span>
          {phase === "speaking" && (
            <div className="sound-waves">
              <span /><span /><span /><span />
            </div>
          )}
        </div>
        <div className="question-bubble">
          {phase === "loading" ? (
            <div className="loading-dots"><span /><span /><span /></div>
          ) : (
            <p>{question}</p>
          )}
        </div>
      </div>

      {/* User Answer area */}
      <div className="answer-section">
        {/* Mode toggle — only show if STT is available */}
        {SpeechRecognitionAPI && (phase === "listening" || phase === "processing") && (
          <div className="input-mode-toggle">
            <button
              className={`mode-btn ${inputMode === "voice" ? "active" : ""}`}
              onClick={() => {
                if (inputMode === "text") {
                  setInputMode("voice");
                  if (phase === "listening") startListening();
                }
              }}
            >
              🎤 Voice
            </button>
            <button
              className={`mode-btn ${inputMode === "text" ? "active" : ""}`}
              onClick={() => {
                if (inputMode === "voice") {
                  stopListening();
                  setInputMode("text");
                }
              }}
            >
              ⌨️ Type
            </button>
          </div>
        )}

        {/* Voice transcript display */}
        {inputMode === "voice" && (
          <div className={`transcript-box ${phase === "listening" ? "active" : ""}`}>
            <p>
              {transcript}
              {interimTranscript && <span className="interim">{interimTranscript}</span>}
              {!transcript && !interimTranscript && phase === "listening" && (
                <span className="placeholder">Listening... speak your answer</span>
              )}
              {phase === "processing" && <span className="placeholder">Processing your answer...</span>}
            </p>
          </div>
        )}

        {/* Text input */}
        {inputMode === "text" && phase !== "processing" && (
          <textarea
            className="text-answer-input"
            value={typedAnswer}
            onChange={(e) => setTypedAnswer(e.target.value)}
            placeholder="Type your answer here..."
            rows={4}
            onKeyDown={(e) => {
              if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) handleTextSubmit();
            }}
          />
        )}

        {phase === "processing" && inputMode === "text" && (
          <div className="transcript-box">
            <p><span className="placeholder">Processing your answer...</span></p>
          </div>
        )}

        {error && <p className="interview-error">{error}</p>}

        <div className="mic-controls">
          {phase === "listening" && inputMode === "voice" && (
            <>
              <div className="mic-pulse">
                <button className="btn-mic active" aria-label="Microphone active">
                  <svg viewBox="0 0 24 24" fill="currentColor" width="28" height="28">
                    <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm5.91-3c-.49 0-.9.36-.98.85C16.52 14.2 14.47 16 12 16s-4.52-1.8-4.93-4.15c-.08-.49-.49-.85-.98-.85-.61 0-1.09.54-1 1.14.49 3 2.89 5.35 5.91 5.78V20c0 .55.45 1 1 1s1-.45 1-1v-2.08c3.02-.43 5.42-2.78 5.91-5.78.1-.6-.39-1.14-1-1.14z"/>
                  </svg>
                </button>
              </div>
              <button className="btn-submit-answer" onClick={handleStopAndSubmit}>
                Submit Answer →
              </button>
            </>
          )}

          {phase === "listening" && inputMode === "text" && (
            <button
              className="btn-submit-answer"
              onClick={handleTextSubmit}
              disabled={!typedAnswer.trim()}
            >
              Submit Answer →
            </button>
          )}

          {phase === "speaking" && (
            <p className="phase-hint">AI is speaking...</p>
          )}

          {phase === "processing" && (
            <div className="loading-dots"><span /><span /><span /></div>
          )}
        </div>
      </div>
    </div>
  );
}
