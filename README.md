# 🎭 AI Debate Arena

A multi-agent debate system where AI agents with different personalities debate any topic from multiple perspectives. Built with local LLMs (Ollama) - **100% free, no API keys needed**.

![AI Debate Arena](https://img.shields.io/badge/AI-Multi--Agent-blue)
![Python](https://img.shields.io/badge/Python-3.10+-green)
![Next.js](https://img.shields.io/badge/Next.js-14-black)
![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-orange)

## ✨ Features

- **🤖 Multiple AI Agents**: Each agent has a unique personality and perspective
- **🎯 Real-time Streaming**: Watch arguments appear as they're generated
- **🏠 100% Local**: Runs entirely on your machine using Ollama
- **🎨 Beautiful UI**: Modern, animated interface with Tailwind CSS
- **⚙️ Customizable**: Choose agents, number of rounds, any topic
- **💰 Free Forever**: No API costs, no subscriptions

## 🚀 Quick Start

### Prerequisites

1. **Python 3.10+** - [Download](https://python.org)
2. **Node.js 18+** - [Download](https://nodejs.org)
3. **Ollama** - [Download](https://ollama.ai)

### Installation

#### Step 1: Install Ollama and download a model

```bash
# After installing Ollama from https://ollama.ai, run:
ollama pull llama3.2:3b
```

This downloads the Llama 3.2 model (~2GB). Only needed once.

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
2. **Select agents** (2-4 agents with different perspectives)
3. **Choose rounds** (more rounds = deeper debate)
4. **Click "Start Debate"** and watch the AI argue!

### Available Agents

| Agent | Personality |
|-------|-------------|
| 😊 **Alex (Optimist)** | Sees opportunities, focuses on benefits |
| 🤔 **Morgan (Skeptic)** | Questions everything, focuses on risks |
| ⚖️ **Jordan (Pragmatist)** | Balances views, focuses on tradeoffs |
| 💡 **Sam (Innovator)** | Challenges conventions, explores new ideas |
| 🎖️ **Casey (Veteran)** | Experienced perspective, values lessons learned |
| 😈 **Riley (Devil's Advocate)** | Challenges the dominant position |

## 📁 Project Structure

```
debate-agents/
├── backend/
│   ├── agents.py        # Agent definitions and LLM integration
│   ├── arena.py         # Debate orchestration logic
│   ├── server.py        # FastAPI server with streaming
│   └── requirements.txt # Python dependencies
│
├── frontend/
│   ├── app/
│   │   ├── page.tsx     # Main debate interface
│   │   ├── layout.tsx   # App layout
│   │   └── globals.css  # Styles
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
| `/debate` | POST | Start a streaming debate |
| `/debate/sync` | POST | Start debate (non-streaming) |

### Example API Request

```bash
curl -X POST http://localhost:8000/debate \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Is remote work better than office work?",
    "rounds": 2,
    "agent_templates": ["optimist", "skeptic", "pragmatist"]
  }'
```

## 🛠️ Configuration

### Using a Different Model

Edit `backend/agents.py` line 19:

```python
self.model = "llama3.2:3b"  # Change to any Ollama model
```

Available models:
- `llama3.2:3b` - Fast, good quality (recommended)
- `llama3.2:1b` - Faster, lower quality
- `mistral` - Higher quality, needs more RAM
- `phi3:mini` - Very fast, compact

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
- Check if Ollama is installed and running

### "Model not found" error
```bash
ollama pull llama3.2:3b
```

### Slow responses
- Try a smaller model: `ollama pull llama3.2:1b`
- Close other applications to free up RAM

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

## 📝 License

MIT License - feel free to use this for your portfolio!

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai) - Local LLM runtime
- [FastAPI](https://fastapi.tiangolo.com) - Python API framework
- [Next.js](https://nextjs.org) - React framework
- [Tailwind CSS](https://tailwindcss.com) - Styling
- [Framer Motion](https://framer.com/motion) - Animations

---

Built with 💜 for learning and portfolio purposes.

