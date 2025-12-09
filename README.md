# discourse — AI Debate Arena

A sophisticated multi-agent debate system where AI agents with distinct personalities engage in structured debates on any topic. Built with local LLMs via Ollama — **100% free, runs entirely on your machine**.

![AI Debate Arena](https://img.shields.io/badge/AI-Multi--Agent-blue)
![Python](https://img.shields.io/badge/Python-3.10+-green)
![Next.js](https://img.shields.io/badge/Next.js-14-black)
![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-orange)

## ✨ Features

### 🎯 Structured 5-Phase Debates
- **Opening Statements** — Each agent presents their initial perspective
- **Rebuttals** — Agents challenge and respond to each other's arguments
- **Cross-Examination** — Direct questioning between opponents
- **Closing Statements** — Final arguments and summaries
- **Voting & Synthesis** — Agents vote for the most compelling argument + moderator synthesis

### 🤖 12 Unique AI Agents

**Modern Perspectives:**
| Agent | Personality |
|-------|-------------|
| 😊 **The Optimist** | Sees possibility where others see problems, champions progress |
| 🤔 **The Skeptic** | Questions everything, demands evidence over enthusiasm |
| ⚖️ **The Pragmatist** | Cuts through ideology, focuses on what actually works |
| 💡 **The Innovator** | Challenges conventions, explores unconventional solutions |
| 🎖️ **The Veteran** | Pattern recognition from experience, institutional memory |
| 😈 **The Contrarian** | Attacks consensus, stress-tests ideas |

**Philosophers (4 Core Ethical Frameworks + 2 Wildcards):**
| Agent | Framework | Core Question |
|-------|-----------|---------------|
| 📜 **Kant** | Deontologist | "Can this be a universal moral law?" |
| 📊 **Mill** | Utilitarian | "Does this maximize overall wellbeing?" |
| 🏛️ **Aristotle** | Virtue Ethicist | "What would a person of good character do?" |
| ⚖️ **Rawls** | Justice Theorist | "Is this fair behind a veil of ignorance?" |
| ❓ **Socrates** | Dialectician | Probes assumptions through questioning |
| ⚡ **Nietzsche** | Existentialist | Challenges all moral frameworks |

### 🎨 Interactive UI Features
- **Real-time streaming** — Watch arguments appear as they're generated
- **Vote & Pin** — Upvote compelling points, pin key insights
- **Follow-up Questions** — Ask any agent clarifying questions mid-debate
- **Agent Responses** — Request one agent to respond to another
- **Save & Export** — Save debates locally, copy as markdown
- **Keyboard shortcuts** — `Enter` to start, `Esc` to stop

### 💰 100% Free & Private
- Runs entirely on your machine using Ollama
- No API keys, no subscriptions, no data leaves your computer

## 🚀 Quick Start

### Prerequisites

1. **Python 3.10+** — [Download](https://python.org)
2. **Node.js 18+** — [Download](https://nodejs.org)
3. **Ollama** — [Download](https://ollama.ai)

### Installation

#### Step 1: Install Ollama and download a model

```bash
# After installing Ollama from https://ollama.ai, run:
ollama pull mistral:7b
```

This downloads the Mistral 7B model (~4GB). Only needed once.

> **Tip:** For faster responses on lower-end hardware, use `ollama pull llama3.2:3b`

#### Step 2: Set up the Backend

```bash
# Navigate to backend folder
cd backend

# Create virtual environment (recommended)
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### Step 3: Set up the Frontend

```bash
# Navigate to frontend folder
cd frontend

# Install dependencies
npm install
```

### Running the Application

You need **two terminal windows**:

#### Terminal 1: Start the Backend

```bash
cd backend
# Activate venv if not already active
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

uvicorn server:app --reload --port 8000
```

You should see: `Uvicorn running on http://127.0.0.1:8000`

#### Terminal 2: Start the Frontend

```bash
cd frontend
npm run dev
```

You should see: `Local: http://localhost:3000`

#### Step 4: Open in Browser

Go to **http://localhost:3000** and start debating! 🎉

## 🎮 Usage

1. **Enter a topic** or click a sample topic
2. **Select 2-4 agents** — mix and match modern perspectives and philosophers
3. **Choose rounds** (more rounds = deeper debate)
4. **Click "Start"** and watch the structured debate unfold

### Debate Flow

```
📢 Opening Statements → ⚔️ Rebuttals → ❓ Cross-Examination → 🎤 Closing → 🗳️ Voting → 📊 Synthesis
```

### Interactive Controls

| Action | Description |
|--------|-------------|
| ↑/↓ | Vote on arguments |
| 📌 | Pin important insights |
| 💬 | Ask follow-up questions |
| ↩ | Request agent-to-agent responses |
| ⊞/⊟ | Expand/collapse arguments |

## 📁 Project Structure

```
debate-agents/
├── backend/
│   ├── agents.py        # 12 agent definitions + LLM integration
│   ├── arena.py         # 5-phase debate orchestration
│   ├── server.py        # FastAPI server with SSE streaming
│   └── requirements.txt # Python dependencies
│
├── frontend/
│   ├── app/
│   │   ├── page.tsx     # Main debate interface (React + Framer Motion)
│   │   ├── layout.tsx   # App layout
│   │   └── globals.css  # Tailwind styles
│   ├── package.json     # Node dependencies
│   └── ...config files
│
└── README.md
```

## 🔧 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check and API info |
| `/health` | GET | Health status |
| `/templates` | GET | List available agent templates |
| `/debate` | POST | Start a streaming debate (SSE) |
| `/debate/sync` | POST | Start debate (non-streaming) |
| `/followup` | POST | Ask an agent a follow-up question |
| `/respond` | POST | Request agent-to-agent response |

### Example API Request

```bash
curl -X POST http://localhost:8000/debate \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Should we regulate AI development?",
    "rounds": 2,
    "agent_templates": ["kant", "mill", "nietzsche"]
  }'
```

## 🛠️ Configuration

### Using a Different Model

Edit `backend/agents.py` line 25:

```python
self.model = "mistral:7b"  # Change to any Ollama model
```

Available models:
- `mistral:7b` — Default, high quality (recommended)
- `llama3.2:3b` — Faster, good quality
- `llama3.2:1b` — Fastest, lower quality
- `phi3:mini` — Very fast, compact
- `mixtral:8x7b` — Highest quality, needs more RAM

### Adjusting Creativity

Edit `backend/agents.py` in `generate_response()`:

```python
options={
    'temperature': 0.8,  # 0.0-1.0, higher = more creative
    'top_p': 0.9,
}
```

## 🐛 Troubleshooting

### "Connection refused" error
- Make sure the backend is running on port 8000
- Check if Ollama is installed and running (`ollama serve`)

### "Model not found" error
```bash
ollama pull mistral:7b
```

### Slow responses
- Try a smaller model: `ollama pull llama3.2:3b`
- Close other applications to free up RAM
- Ensure Ollama is using GPU if available

### Backend won't start
- Make sure you're in the `backend` folder
- Activate the virtual environment
- Run `pip install -r requirements.txt`

## 🚀 Deployment

### Backend (Railway/Render)

1. Push to GitHub
2. Connect to Railway/Render
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `uvicorn server:app --host 0.0.0.0 --port $PORT`

**Note**: For cloud deployment, you'll need to use a cloud LLM API instead of Ollama.

### Frontend (Vercel)

1. Push to GitHub
2. Import to Vercel
3. Set `NEXT_PUBLIC_API_URL` environment variable to your backend URL

## 🧠 How It Works

1. **Agent System** — Each agent has a unique personality prompt that shapes their reasoning style
2. **Debate Orchestration** — The arena manages turn-taking, context passing, and phase transitions
3. **Streaming Responses** — Server-Sent Events (SSE) deliver arguments in real-time
4. **Local LLM** — Ollama runs the model locally, ensuring privacy and zero cost

## 📝 License

MIT License — feel free to use this for your portfolio, learning, or commercial projects.

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai) — Local LLM runtime
- [FastAPI](https://fastapi.tiangolo.com) — Python API framework
- [Next.js](https://nextjs.org) — React framework
- [Tailwind CSS](https://tailwindcss.com) — Utility-first CSS
- [Framer Motion](https://framer.com/motion) — Animation library

---

Built with 💜 for exploring multi-agent AI systems
