# J.A.R.V.I.S — Just A Rather Very Intelligent System

<div align="center">

![JARVIS](https://img.shields.io/badge/JARVIS-AI%20OS-00d4ff?style=for-the-badge&logo=robot&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-LLaMA%203.3%2070B-F55036?style=for-the-badge&logo=meta&logoColor=white)

**An Iron Man–grade agentic AI OS built from scratch.**  
Multi-agent architecture · Real-time voice biometrics · Intruder photo capture · Full browser control · Live data · Website builder

</div>

---

## ✨ Feature Highlights

### 🤖 Multi-Agent Architecture
A central router (`brain.py`) classifies every voice/text command using LLaMA 3.3 70B and routes it to one of 7 specialized agents:

| Agent | Responsibility |
|---|---|
| **Chat** | General conversation, Q&A, memory |
| **Web** | Web search and live browsing |
| **Automation** | App control, WhatsApp, Instagram, YouTube, Chrome navigation |
| **System** | OS-level operations, screenshots, file handling |
| **Live Data** | Weather, stocks, crypto, news, cricket scores |
| **Builder** | Generate complete websites from a single voice prompt |
| **Heartbeat** | Optical heart-rate measurement via webcam |

---

### 🔐 Multi-Layer Biometric Security

All three layers must pass before JARVIS activates:

```
[ Password Gate ] → [ Face Recognition (LBPH) ] → [ Voice Passphrase (MFCC) ]
```

| Layer | Technology | How It Works |
|---|---|---|
| **1. Password** | Passphrase entry | Standard gate |
| **2. Face (Dual-Layer)** | OpenCV Haar Cascade + LBPH | Detects face → verifies it's Raj |
| **3. Voice (MFCC)** | 26-dim Mel Cepstral Coefficients | Cosine similarity ≥ 0.82 |

**If any unauthorized user speaks a command:**
- Screen locks instantly via `pmset displaysleepnow`
- Webcam silently captures an intruder photo
- Photo saved to `intruder_log/` with timestamp
- Frontend Biometrics Dashboard alerts in real-time

---

### 📷 Intruder Photo Capture System

When a non-Raj voice is detected during a command:
1. OpenCV opens the webcam silently (no UI shown)
2. Captures and saves `intruder_YYYYMMDD_HHMMSS.jpg`
3. Locks the macOS screen
4. Emits `intruder_alert` WebSocket event to frontend
5. Biometrics Dashboard auto-opens with the event log

---

### 🌐 Full Chrome Browser Voice Control

Say natural commands to control Chrome without touching the keyboard:

| Voice Command | Action |
|---|---|
| *"scroll down / up"* | Scrolls the page |
| *"scroll to top / bottom"* | Jumps to page edges |
| *"go back / forward"* | Browser navigation |
| *"refresh"* | Reloads the page |
| *"new tab"* | Opens a new Chrome tab |
| *"zoom in / out / reset zoom"* | Adjusts browser zoom |
| *"find on page [text]"* | Opens Ctrl+F with search term |
| *"next tab / previous tab"* | Switches Chrome tabs |
| *"fullscreen"* | Toggles F11 fullscreen |
| *"close [YouTube/Instagram/...]"* | Closes that specific tab |
| *"close all tabs"* | Closes every Chrome tab |

---

### 📊 Biometrics Dashboard (Real-Time HUD)

A cyberpunk security panel embedded in the JARVIS UI:
- **Voice Score Gauge** — cosine similarity percentage
- **Face Score Gauge** — LBPH confidence score
- **Overall Security Level** — HIGH / MEDIUM / LOW with animated bar
- **Live Audio Visualizer** — FFT canvas visualization of mic input
- **Voice Threshold Slider** — tune sensitivity from 0.60 to 0.99
- **LBPH Face Registration** — one-click webcam training (30 samples)
- **Intruder Event Log** — all intrusion photos with timestamps, auto-refresh

---

### 🎙️ Voice Interface

- Continuous listening via Web Speech API (Chrome)
- MFCC voiceprint verification on every command
- Interrupt mid-response with a new command
- Microsoft Edge Neural TTS for natural JARVIS voice
- Male / Female voice toggle

---

### 🧠 Memory System

| Type | Storage | Scope |
|---|---|---|
| **Short-term** | In-memory session context | Per session |
| **Long-term** | Fernet-encrypted `.enc` files | Survives restarts |

---

### 📡 Live Data

- 🌤️ Weather via OpenWeatherMap API
- 📈 Stock prices via `yfinance`
- 💱 Currency exchange + gold prices
- 📰 News headlines via NewsAPI
- 🏏 Live cricket scores

---

### 🛠️ Automation Capabilities

- Control **WhatsApp Web** — search contacts, send messages, voice/video calls
- Control **Instagram** — open profiles, send DMs
- **YouTube** — search, play songs, open videos
- Control **VS Code, GitHub, LinkedIn, Portfolio**
- Open any website by name or URL
- **Screenshot** capture and save
- **Website builder** — generate HTML/CSS/JS sites from one voice command
- **AI Assistants** — open ChatGPT/Gemini/Claude and ask them questions by voice

---

### 🚀 Auto-Start on Login

JARVIS launches automatically when the Mac boots:
- `com.raj.jarvis.plist` — LaunchAgent plist
- `jarvis_autostart.sh` — startup orchestration script
- `install_autostart.sh` / `uninstall_autostart.sh` — one-command setup

---

## 🏗️ Tech Stack

| Layer | Technologies |
|---|---|
| **AI / LLM** | Groq API, LLaMA 3.3 70B, LLaMA 3.1 8B |
| **Backend** | FastAPI, Python-SocketIO, Uvicorn |
| **Frontend** | React 18, Vite, TailwindCSS |
| **Face Recognition** | OpenCV (Haar Cascade + LBPH) |
| **Voice Biometrics** | MFCC, DCT, Cosine Similarity (pure Python/NumPy) |
| **Voice Output** | Edge TTS (Neural), Web Speech API |
| **Live Data** | OpenWeatherMap, yfinance, NewsAPI |
| **Security** | Fernet encryption, Socket.IO auth tokens, intruder photo log |
| **Automation** | PyAutoGUI, AppleScript, webbrowser |
| **Methodology** | Agile (iterative sprints) |

---

## 🏛️ Architecture

```
User (Voice / Text)
        │
        ▼
 ┌─────────────────────┐
 │   React Frontend    │  ← Sci-fi HUD, 3D Globe, Biometrics Dashboard
 │   Vite + Tailwind   │
 └────────┬────────────┘
          │  Socket.IO (real-time, bidirectional)
          ▼
 ┌─────────────────────┐       ┌────────────────────────────┐
 │  FastAPI Backend    │──────►│   Security Fast-Path       │
 │  main.py           │       │   Voice biometrics check   │
 └────────┬────────────┘       │   Intruder photo capture  │
          │                    └────────────────────────────┘
          ▼
 ┌─────────────────────┐
 │   brain.py Router   │  ← LLM intent classification
 └──┬──┬──┬──┬──┬──┬───┘
    │  │  │  │  │  │
    ▼  ▼  ▼  ▼  ▼  ▼
  Chat Web Auto Sys Live Builder
  Agent Agent Agent Agent Data  Agent
    │                      │
    └──────────────────────┘
               │
               ▼
       Groq API → LLaMA 3.3 70B
```

---

## 📁 Project Structure

```
jarvis_main/
├── backend/
│   ├── main.py                    # FastAPI + Socket.IO server
│   ├── brain.py                   # LLM-powered command router
│   ├── face_auth.py               # Dual-layer face auth (Haar + LBPH)
│   ├── voice.py                   # Edge TTS voice output
│   ├── register_face.py           # Face model training CLI
│   ├── requirements.txt
│   └── agents/
│       ├── chat_agent.py          # Conversation + long-term memory
│       ├── web_agent.py           # Web search
│       ├── automation_agent.py    # App/browser/Chrome control
│       ├── system_agent.py        # OS-level operations
│       ├── live_agent.py          # Weather, stocks, news, cricket
│       ├── builder_agent.py       # Website generator
│       ├── heartbeat_agent.py     # Optical heart-rate monitor
│       ├── crew_agent.py          # Multi-agent CrewAI newsletter
│       ├── security_agent.py      # Intrusion detection + photo capture
│       ├── voice_auth.py          # MFCC voiceprint biometrics
│       └── face_data/
│           ├── lbph_face_model.xml  # Trained face model
│           ├── voice_profile.npy    # Raj's voice signature
│           └── intruder_log/        # Timestamped intruder photos
├── frontend/
│   └── src/
│       ├── App.jsx                # Main app + PasswordGate + JarvisApp
│       ├── components/
│       │   ├── BiometricsDashboard.jsx  # Security HUD widget
│       │   ├── ConsentModal.jsx         # Startup consent popup
│       │   ├── ActivityMonitor.jsx
│       │   ├── SystemLog.jsx
│       │   ├── Globe3D.jsx
│       │   ├── IronManTopLeft.jsx
│       │   ├── NeuralCore3D.jsx
│       │   ├── DocumentAnalysis.jsx
│       │   ├── GenderDetection.jsx
│       │   └── VoiceSelector.jsx
│       └── index.css
├── chrome_extension/              # Chrome extension for tab control
├── com.raj.jarvis.plist           # macOS LaunchAgent (auto-start)
├── jarvis_autostart.sh            # Startup orchestration
├── install_autostart.sh           # One-command install
└── uninstall_autostart.sh         # One-command uninstall
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- macOS (primary target; Windows partially supported)
- A Groq API key (free at [console.groq.com](https://console.groq.com))

### Installation

**1. Clone the repository**
```bash
git clone https://github.com/RAJ-15012006/jarvis_agentic_ai.git
cd jarvis_agentic_ai
```

**2. Backend setup**
```bash
cd backend
pip install -r requirements.txt
```

**3. Configure environment variables**
```bash
# Create .env in the project root
GROQ_API_KEY=your_groq_api_key
OPENWEATHER_API_KEY=your_openweather_key
NEWS_API_KEY=your_newsapi_key
SOCKET_SECRET=jarvis-local-secret
```

**4. Frontend setup**
```bash
cd ../frontend
npm install
npm run build
```

**5. Run JARVIS**
```bash
# From project root:
cd backend
python main.py
```
Open `http://localhost:8000` in Chrome.

**6. First-time biometric setup**
- **Voice:** Complete the 3-sample voice registration in the login screen
- **Face:** Click **"📷 Register Raj's Face"** in the Biometrics Dashboard → look at the webcam for ~30 seconds

**7. (Optional) Auto-start on Mac login**
```bash
chmod +x install_autostart.sh
./install_autostart.sh
```

---

## 📚 Libraries Used (20+)

`fastapi` · `python-socketio` · `uvicorn` · `groq` · `opencv-python` · `edge-tts` · `cryptography` · `yfinance` · `requests` · `pyautogui` · `pywhatkit` · `numpy` · `scipy` · `pillow` · `python-dotenv` · `crewai` · `pyperclip` · `pypdf` · `websocket-client` · `aiofiles`

---

## ⚙️ Key Technical Highlights

- **Real-time bidirectional** communication via Socket.IO between React and FastAPI
- **Sub-second LLM responses** using Groq's inference infrastructure with LLaMA 3.3 70B
- **MFCC voiceprint biometrics** — 26-dimensional DCT feature vector with cosine similarity matching
- **Dual-layer face recognition** — Haar Cascade detection + LBPH identity verification
- **Intruder logging** — silent webcam capture on any unauthorized voice with timestamp audit trail
- **Chrome browser control** — 15+ voice commands mapped to keyboard shortcuts via PyAutoGUI
- **Fernet symmetric encryption** for secure long-term memory persistence
- **Optical heart-rate detection** — rPPG algorithm using webcam color channel analysis
- **Multi-agent AI newsletter** — CrewAI orchestrated multi-agent research pipeline
- **Voice interruption** — new commands cancel ongoing TTS mid-sentence instantly
- **Auto-start daemon** — LaunchAgent plist for automatic startup on macOS login

---

## 🗺️ Roadmap

- [ ] Screen reading — understand what's on screen via vision AI
- [ ] Email integration — read/compose emails by voice
- [ ] Calendar management — schedule meetings by voice
- [ ] Mobile companion app (React Native)
- [ ] Plugin system for custom agent extensions
- [ ] Multi-user profiles with isolated biometric auth per user
- [ ] Proactive suggestions — JARVIS speaks first based on calendar/habits

---

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

<div align="center">

*"Sometimes you gotta run before you can walk."* — Tony Stark

**Built by [Raj Samrendra Kumar](https://raj-personal-portfolio.netlify.app/)**

</div>
