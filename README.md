# J.A.R.V.I.S — Just A Rather Very Intelligent System

An agentic AI assistant built from scratch with a multi-agent architecture, real-time voice interface, 3-layer biometric security, and live data capabilities — powered by Meta's LLaMA 3.3 70B via Groq API.

---

## Features

### 🤖 Multi-Agent Architecture
A central router (`brain.py`) classifies every command and routes it to one of 6 specialized agents:

| Agent | Responsibility |
|---|---|
| **Chat** | General conversation and Q&A |
| **Web** | Web search and browsing |
| **Automation** | App control, WhatsApp, Instagram, YouTube |
| **System** | OS-level operations, screenshots, file handling |
| **Live Data** | Weather, stocks, crypto, news, cricket scores |
| **Builder** | Generate complete websites from a single voice prompt |

### 🔐 3-Layer Security Authentication
All three layers must pass before JARVIS activates:
- **Password** — standard passphrase entry
- **Face Recognition** — OpenCV LBPH algorithm trained on 500 samples across 5 angles
- **Voice Passphrase** — verified using Web Speech API

### 🎙️ Voice Interface
- Continuous listening via Web Speech API
- Interrupt mid-response with a new command
- Microsoft Edge Neural TTS for natural, JARVIS-like voice output

### 🧠 Memory System
- **Short-term** — per-session conversation context
- **Long-term** — encrypted memory persisted to disk using Fernet encryption; survives restarts

### 📡 Live Data
- Weather via OpenWeatherMap API
- Stock prices via `yfinance`
- Currency exchange rates and gold prices
- News headlines via NewsAPI
- Live cricket scores

### 🛠️ Automation Capabilities
- Control WhatsApp, Instagram, YouTube
- Open desktop applications
- Take screenshots
- Type into Notepad and other apps
- Build complete websites (HTML/CSS/JS) from a single voice command

---

## Tech Stack

| Layer | Technologies |
|---|---|
| **AI / LLM** | Groq API, LLaMA 3.3 70B |
| **Backend** | FastAPI, Socket.IO, Python |
| **Frontend** | React, Vite, TailwindCSS |
| **Face Recognition** | OpenCV (LBPH Algorithm) |
| **Voice** | Edge TTS, Web Speech API |
| **Live Data** | OpenWeatherMap, yfinance, NewsAPI |
| **Security** | Fernet encryption, Socket auth tokens |
| **SDLC** | Agile (iterative development) |

---

## Architecture Overview

```
User (Voice / Text)
        │
        ▼
  React Frontend  ◄──── Socket.IO (real-time) ────►  FastAPI Backend
        │                                                     │
        ▼                                                     ▼
  Web Speech API                                        brain.py (Router)
  Edge TTS                                                    │
                                    ┌───────────────┬─────────┴──────────┬────────────────┐
                                    ▼               ▼                    ▼                ▼
                               Chat Agent      Web Agent         Automation Agent   Builder Agent
                               Live Data Agent System Agent
                                    │
                                    ▼
                           Groq API → LLaMA 3.3 70B
```

---

## Project Structure

```
jarvis/
├── backend/
│   ├── main.py              # FastAPI + Socket.IO server
│   ├── brain.py             # Command router / classifier
│   ├── agents/
│   │   ├── chat_agent.py
│   │   ├── web_agent.py
│   │   ├── automation_agent.py
│   │   ├── system_agent.py
│   │   ├── live_data_agent.py
│   │   └── builder_agent.py
│   ├── security/
│   │   ├── face_recognition.py
│   │   └── voice_auth.py
│   └── memory/
│       ├── short_term.py
│       └── long_term.py     # Fernet-encrypted persistent memory
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/      # Sci-fi HUD interface components
│   │   └── hooks/           # Voice input / socket hooks
│   ├── index.html
│   └── vite.config.js
├── requirements.txt
├── package.json
└── README.md
```

---

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- Groq API key
- OpenWeatherMap API key
- NewsAPI key

### Installation

**1. Clone the repository**
```bash
git clone https://github.com/yourusername/jarvis.git
cd jarvis
```

**2. Backend setup**
```bash
cd backend
pip install -r requirements.txt
```

**3. Configure environment variables**
```bash
cp .env.example .env
# Add your API keys to .env
```

```
GROQ_API_KEY=your_groq_key
OPENWEATHER_API_KEY=your_openweather_key
NEWS_API_KEY=your_newsapi_key
```

**4. Train face recognition model**
```bash
python security/face_recognition.py --train
# Follow on-screen instructions to capture 500 samples
```

**5. Frontend setup**
```bash
cd ../frontend
npm install
```

**6. Run JARVIS**

Terminal 1 — Backend:
```bash
cd backend
uvicorn main:app --reload
```

Terminal 2 — Frontend:
```bash
cd frontend
npm run dev
```

Open `http://localhost:5173` and complete the 3-layer authentication to activate JARVIS.

---

## Libraries Used (15+)

`fastapi` · `python-socketio` · `groq` · `opencv-python` · `edge-tts` · `cryptography` · `yfinance` · `requests` · `pyautogui` · `pyperclip` · `uvicorn` · `python-dotenv` · `numpy` · `pillow` · `selenium`

---

## Development Methodology

Built following **Agile methodology** — features developed and tested iteratively across multiple sprints, with continuous integration of user feedback and incremental capability expansion.

---

## Key Technical Highlights

- **Real-time bidirectional communication** via Socket.IO between React frontend and FastAPI backend
- **Sub-second LLM responses** achieved using Groq's inference infrastructure with LLaMA 3.3 70B
- **LBPH face recognition** trained on 500 images across 5 facial angles for high accuracy
- **Fernet symmetric encryption** for secure long-term memory persistence
- **Agent routing** via LLM-based intent classification in `brain.py`
- **Voice interruption** — new commands cancel ongoing TTS mid-sentence

---

## Future Improvements

- [ ] Add memory summarization for long-term context compression
- [ ] Integrate vision capabilities for screen understanding
- [ ] Mobile companion app
- [ ] Plugin system for custom agent extensions
- [ ] Multi-user profile support with isolated memory per user

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

> *"Sometimes you gotta run before you can walk."* — Tony Stark
