# miCoach — AI-Powered Developer Coaching Platform

miCoach is a personalized learning platform for software developers. It analyzes your CV and GitHub projects to generate a tailored skill roadmap, then guides you through it via AI mentoring, coding exercises, and mock interviews.

## Features

- **Onboarding analysis** — Upload your CV and GitHub links; the AI evaluates your current skills and career goals
- **Personalized roadmap** — A structured, project-based learning path generated for your specific career track
- **AI mentor chat** — Ongoing conversational guidance with full history context
- **Coding exercises** — AI-generated exercises in Python or JavaScript, matched to your level, with live code execution and feedback
- **Mock interviews** — 5-question AI-driven interviews with scoring and detailed feedback
- **Roadmap progression** — Submit GitHub projects to unlock the next unit; the AI evaluates whether your project meets the requirements
- **Text-to-speech** — ElevenLabs integration for audio responses

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19 + Vite, React Router, Monaco Editor |
| Backend | FastAPI, SQLAlchemy, SQLite |
| Auth | JWT + bcrypt |
| AI | OpenAI-compatible endpoint (Ollama local or any external API) |
| TTS | ElevenLabs API |
| Infra | Docker Compose |

---

## Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose

### 1. Configure environment

Create `backend/.env`:

```env
# AI model — choose one of the options below
AI_MODEL=your-model-name-here
AI_MODEL_BASE_URL=your-model-url-here
AI_MODEL_API_KEY=your_api_key_heres

# Or use a local Ollama model (see "Running with local model" below)
# AI_MODEL=qwen2.5:7b
# AI_MODEL_BASE_URL=http://ollama:11434/v1
# AI_MODEL_API_KEY=ollama

# App
SECRET_KEY=change-this-to-a-random-secret-key
DATABASE_URL=sqlite:///./mycoach.db
UPLOAD_DIR=uploads

# Optional: ElevenLabs text-to-speech
ELEVENLABS_API_KEY=your_elevenlabs_key
ELEVENLABS_AGENT_ID=your_agent_id
```

### 2. Run with an external AI API (default)

```bash
docker compose up --build
```

### 3. Run with a local Ollama model

This starts an extra Ollama container that downloads and serves `qwen2.5:7b` locally. Make sure your `backend/.env` points to `http://ollama:11434/v1`.

```bash
docker compose --profile local up --build
```

> The first run will pull the model (~4 GB). Subsequent starts reuse the cached volume.

### 4. Open the app

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API docs | http://localhost:8000/docs |

---

## Development (without Docker)

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## Project Structure

```
miCoach-Biohackers/
├── backend/
│   ├── main.py            # FastAPI app entry point
│   ├── models.py          # SQLAlchemy models
│   ├── routes/            # Auth, mentor, exercises, interview, roadmap
│   ├── services/
│   │   └── ai.py          # AI client (OpenAI-compatible)
│   └── .env               # Environment config (not committed)
├── frontend/
│   └── src/
│       ├── pages/         # Landing, Login, Register, Dashboard, Practice, Interview
│       └── components/
├── docker-compose.yml
└── README.md
```

## API Overview

| Route | Description |
|-------|-------------|
| `POST /api/auth/register` | Register with CV upload and GitHub links |
| `POST /api/auth/login` | Login, returns JWT |
| `POST /api/mentor/onboard` | Trigger AI skill analysis and roadmap generation |
| `POST /api/mentor/chat` | Send a message to the AI mentor |
| `POST /api/exercises/generate` | Generate a coding exercise |
| `POST /api/exercises/run` | Run code against test cases |
| `POST /api/interview/start` | Start a mock interview session |
| `POST /api/roadmap/units/{id}/submit` | Submit a GitHub project for unit evaluation |
