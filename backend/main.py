import os
import sys
import asyncio
import uvicorn
import datetime
import time
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import socketio

# Add backend directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from brain import route_command
from agents.system_agent import execute_system_command
from agents.web_agent import web_search
from agents.automation_agent import execute_automation
from agents.chat_agent import chat_response, clear_session, predict_user_needs
from agents.live_agent import handle_live_query
from agents.builder_agent import build_website, is_build_request, extract_build_prompt
from agents.heartbeat_agent import measure_heart_rate
from agents.security_agent import (
    is_intrusion_attempt,
    is_shutdown_command,
    is_close_all_tabs_command,
    lock_screen,
    lock_screen_with_photo,
    shutdown_system,
    close_all_chrome_tabs,
    get_intruder_log,
    INTRUDER_LOG_DIR,
)
from voice import speak_text, interrupt, set_voice
from typing import List

# Safe auto-installer for pypdf (required for resume/PDF uploads)
try:
    import pypdf
except ImportError:
    import subprocess
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "pypdf"])
        import pypdf
    except Exception as e:
        print(f"Warning: Failed to auto-install pypdf: {e}")

from agents.crew_agent import run_tech_digest_crew
# ── NEW AGENTS (Mega-Upgrade) ─────────────────────────────────────────────────
from agents.screen_agent import analyze_screen, is_screen_command
from agents.emotion_agent import (
    detect_emotion, emotion_check_response, get_current_emotion_state, is_emotion_command
)
from agents.gmail_agent import handle_gmail_command, is_gmail_command
from agents.calendar_agent import handle_calendar_command, is_calendar_command
from agents.spotify_agent import handle_spotify_command, is_spotify_command
from agents.translation_agent import translate_command, is_translation_command
from agents.github_stats_agent import handle_github_command, is_github_command
from agents.proactive_agent import (
    start_proactive_engine, get_pending_proactive_message,
    trigger_morning_briefing, is_briefing_command
)

# JARVIS AI OS Main Server
app = FastAPI(title="JARVIS AI OS", version="1.0.0")

ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://jarvis.weblog:8000",
    "http://jarvis.weblog:5173",
    "http://jarvis.weblog",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)

@app.get("/api")
async def root():
    return {"status": "JARVIS is online", "core": "running"}

# ── Global Microphone Listener & Execution Engine (Standalone Process Helper) ─────
main_loop = None

async def execute_global_command(command: str):
    """Executes a voice command globally from the background mic thread."""
    global system_unlocked, _command_executing
    if not system_unlocked:
        print("[SECURITY] Voice command ignored because system is locked.")
        return
    if _command_executing:
        print("[GLOBAL CMD] Skipped — another command is already executing.")
        return
    _command_executing = True
    try:
        await _execute_global_command_inner(command)
    finally:
        _command_executing = False

async def _execute_global_command_inner(command: str):
    global system_unlocked
    if not system_unlocked:
        print("[SECURITY] Voice command ignored because system is locked.")
        return
    now = datetime.datetime.now().strftime("%H:%M:%S")
    # Interrupt any active speech
    interrupt()
    
    # Check for immediate STOP/MUTE commands
    if command.lower().strip() in ["stop", "stop speaking", "be quiet", "shut up", "mute"]:
        await sio.emit('system_log', {'time': now, 'type': 'jarvis', 'message': "Muted."})
        await sio.emit('activity_state', {'state': 'STANDBY'})
        return

    # Check for immediate COME BACK command to return to JARVIS page
    if command.lower().strip() in ["come back", "go back to jarvis", "open jarvis page"]:
        await sio.emit('system_log', {'time': now, 'type': 'jarvis', 'message': "Coming back to my home screen, Raj."})
        await sio.emit('activity_state', {'state': 'SPEAKING'})
        if sys.platform == "darwin":
            script = """
            tell application "Google Chrome"
                activate
                set foundTab to false
                repeat with w in windows
                    set tabIndex to 1
                    repeat with t in tabs of w
                        if (URL of t contains "localhost:8000") or (URL of t contains "127.0.0.1:8000") or (URL of t contains "jarvis.weblog") then
                            set active tab index of w to tabIndex
                            set index of w to 1
                            set foundTab to true
                            exit repeat
                        end if
                        set tabIndex to tabIndex + 1
                    end repeat
                    if foundTab then exit repeat
                end repeat
            end tell
            """
            import subprocess
            subprocess.run(["osascript", "-e", script])
        await asyncio.to_thread(speak_text, "Welcome back, Raj.")
        await sio.emit('activity_state', {'state': 'STANDBY'})
        return
        
    # Broadcast command to all connected frontend clients so the log updates
    await sio.emit('system_log', {'time': now, 'type': 'user', 'message': f"[Voice] {command}"})
    await sio.emit('activity_state', {'state': 'PROCESSING'})
    
    if is_shutdown_command(command):
        await sio.emit('system_log', {'time': now, 'type': 'jarvis', 'message': "Shutdown capability is disabled for safety, Sir."})
        await sio.emit('activity_state', {'state': 'SPEAKING'})
        await asyncio.to_thread(speak_text, "Shutdown capability is disabled for safety, Sir.")
        return

    if is_close_all_tabs_command(command):
        await sio.emit('system_log', {'time': now, 'type': 'jarvis', 'message': "Closing all browser tabs, Sir."})
        await sio.emit('activity_state', {'state': 'PROCESSING'})
        result = await asyncio.to_thread(close_all_chrome_tabs)
        await sio.emit('system_log', {'time': now, 'type': 'jarvis', 'message': result})
        await sio.emit('activity_state', {'state': 'SPEAKING'})
        await asyncio.to_thread(speak_text, result)
        await sio.emit('activity_state', {'state': 'STANDBY'})
        return

    # Check for in-page navigation commands (scroll, zoom, refresh, etc.)
    from agents.automation_agent import _chrome_nav
    nav_response = await asyncio.to_thread(_chrome_nav, command)
    if nav_response:
        event_name = None
        event_data = None
        if isinstance(nav_response, tuple):
            response, event_name, event_data = nav_response
        else:
            response = nav_response

        await sio.emit('system_log', {'time': now, 'type': 'jarvis', 'message': response})
        await sio.emit('activity_state', {'state': 'SPEAKING'})
        if event_name:
            await sio.emit(event_name, event_data)
        await asyncio.to_thread(speak_text, response)
        await sio.emit('activity_state', {'state': 'STANDBY'})
        return

    # --- Heartbeat check ---
    if any(w in command.lower() for w in ["heartbeat", "heart rate", "heart beat",
                                           "pulse", "bpm", "check my heart"]):
        await sio.emit('activity_state', {'state': 'PROCESSING'})
        await sio.emit('system_log', {'time': now, 'type': 'jarvis',
                        'message': 'Raj, starting heart rate scan. Look at the camera and stay still for 15 seconds.'})
        await asyncio.to_thread(speak_text, 'Starting heart rate scan. Look at the camera and stay still, Raj.')
        heart_response = await asyncio.to_thread(measure_heart_rate)
        await sio.emit('activity_state', {'state': 'SPEAKING'})
        await sio.emit('system_log', {'time': now, 'type': 'jarvis', 'message': heart_response})
        await asyncio.to_thread(speak_text, heart_response)
        await sio.emit('activity_state', {'state': 'STANDBY'})
        return

    # Normal routing
    route_info = route_command(command)
    agent_type = route_info.get("agent")
    agent_name_upper = agent_type.upper() if agent_type else "UNKNOWN"
    await sio.emit('system_log', {'time': now, 'type': 'system', 'message': f"ROUTING TO {agent_name_upper} AGENT"})
    
    response = ""
    tab_url = None
    try:
        if agent_type == "system":       response = await asyncio.to_thread(execute_system_command, command)
        elif agent_type == "web":
            result = await asyncio.to_thread(web_search, command)
            if isinstance(result, tuple):
                response, tab_url = result
            else:
                response = result
        elif agent_type == "automation":
            result = await asyncio.to_thread(execute_automation, command)
            if isinstance(result, tuple):
                response, tab_url = result
            else:
                response = result
        elif agent_type == "screen":     response = await asyncio.to_thread(analyze_screen, command)
        elif agent_type == "gmail":      response = await asyncio.to_thread(handle_gmail_command, command)
        elif agent_type == "calendar":   response = await asyncio.to_thread(handle_calendar_command, command)
        elif agent_type == "spotify":    response = await asyncio.to_thread(handle_spotify_command, command)
        elif agent_type == "translation": response = await asyncio.to_thread(translate_command, command)
        elif agent_type == "github":     response = await asyncio.to_thread(handle_github_command, command)
        elif agent_type == "proactive":  response = await asyncio.to_thread(trigger_morning_briefing)
        else:                            response = chat_response(command, "global")
    except Exception as e:
        response = f"Sir, I encountered a critical error: {e}"
        
    await sio.emit('activity_state', {'state': 'SPEAKING'})
    await sio.emit('system_log', {'time': now, 'type': 'jarvis', 'message': response})
    if tab_url:
        import webbrowser
        webbrowser.open(tab_url)
        await sio.emit('open_tab', {'url': tab_url, 'backend_opened': True})
    
    await asyncio.to_thread(speak_text, response)
    await sio.emit('activity_state', {'state': 'STANDBY'})

from fastapi import Request
@app.post("/api/voice-command")
async def voice_command_endpoint(request: Request):
    """Receives voice commands from the standalone voice listener process."""
    global system_unlocked
    if not system_unlocked:
        return {"success": False, "error": "System is locked. Authentication required."}
        
    # Ignore commands from the background mic if Jarvis is currently speaking (feedback prevention)
    from voice import is_speaking
    if is_speaking():
        print("[VOICE COMMAND] Ignored voice command since Jarvis is speaking.")
        return {"success": False, "error": "Jarvis is speaking"}

    try:
        data = await request.json()
        command = data.get("command", "").strip()
        if not command:
            return {"success": False, "error": "Empty command"}
            
        if main_loop:
            asyncio.run_coroutine_threadsafe(
                execute_global_command(command),
                main_loop
            )
            return {"success": True, "message": "Command queued"}
        else:
            return {"success": False, "error": "Main event loop not initialized"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.on_event("startup")
async def startup_event():
    """Start background services when the server boots."""
    global main_loop
    main_loop = asyncio.get_event_loop()
    
    import threading
    import subprocess
    import sys
    
    # Start proactive engine in background
    threading.Thread(target=start_proactive_engine, daemon=True).start()
    print("[STARTUP] Proactive engine started.")
    
    # Start global microphone listener as a standalone OS process to prevent uvicorn deadlock
    try:
        # Prevent duplicate background listeners by killing any orphans first
        subprocess.run(["pkill", "-f", "global_voice_listener.py"], capture_output=True)
        time.sleep(0.5)
        
        listener_script = os.path.join(os.path.dirname(__file__), "global_voice_listener.py")
        subprocess.Popen([sys.executable, listener_script], close_fds=True)
        print("[STARTUP] Standalone global voice listener process spawned successfully (cleaned orphans).")
    except Exception as e:
        print(f"[STARTUP ERROR] Could not spawn standalone voice listener: {e}")


@app.get("/api/speaking-status")
async def speaking_status():
    """Returns whether JARVIS is currently speaking — used by global_voice_listener to prevent TTS feedback."""
    from voice import is_speaking
    return {"speaking": is_speaking()}

# Heartbeat state for global microphone listener
last_listener_heartbeat = 0.0

@app.post("/api/listener-heartbeat")
async def listener_heartbeat():
    global last_listener_heartbeat
    last_listener_heartbeat = time.time()
    return {"status": "ok"}

@app.get("/api/listener-status")
async def listener_status():
    global last_listener_heartbeat
    is_active = (time.time() - last_listener_heartbeat) < 15.0
    return {"active": is_active, "last_seen": last_listener_heartbeat}

@app.post("/api/listener-restart")
async def listener_restart():
    try:
        import subprocess
        import sys
        # Kill existing listener
        subprocess.run(["pkill", "-f", "global_voice_listener.py"], capture_output=True)
        time.sleep(0.5)
        # Spawn a new listener
        listener_script = os.path.join(os.path.dirname(__file__), "global_voice_listener.py")
        subprocess.Popen([sys.executable, listener_script], close_fds=True)
        return {"success": True, "message": "Global listener restarted successfully"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/recommendation")
async def get_recommendation():
    """Returns a machine-learning powered prediction of user needs."""
    if not system_unlocked:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="System locked")
    import asyncio
    prediction = await asyncio.to_thread(predict_user_needs)
    return {"recommendation": prediction}

auth_just_completed = False

from fastapi import Request, File, UploadFile
@app.post("/api/voice")
async def update_voice(request: Request):
    global auth_just_completed
    data = await request.json()
    gender = data.get("gender", "male")
    set_voice(gender)
    # Only trigger welcome greeting if this is a fresh auth selection (not a reconnect sync)
    if data.get("auth_complete", False):
        auth_just_completed = True
    return {"status": "success", "voice": gender}

@app.post("/api/update")
async def update_system():
    """Simulates a hot-patch/update to the core systems."""
    if not system_unlocked:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="System locked")
    try:
        from voice import speak_text
        # Play completion audio
        await asyncio.to_thread(speak_text, "Core update completed successfully, Sir. All systems are running on the latest version.")
        return {"success": True, "message": "Core update completed."}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/voice-status")
async def voice_status():
    """Checks if Raj's voice profile is registered."""
    try:
        from agents.voice_auth import VOICE_PROFILE_PATH
        import os
        return {"registered": os.path.exists(VOICE_PROFILE_PATH)}
    except Exception as e:
        return {"registered": False, "error": str(e)}

@app.get("/api/face-auth")
async def face_auth():
    """Run face authentication — returns {verified: bool} after OpenCV webcam check."""
    try:
        from face_auth import run_face_auth
        result = await asyncio.to_thread(run_face_auth)
        return result
    except Exception as e:
        return {"verified": False, "error": str(e)}

@app.post("/api/voice-register")
async def voice_register(files: List[UploadFile] = File(...)):
    """Registers Raj's voice profile using 3 voice WAV samples."""
    try:
        from agents.voice_auth import register_voice_profile
        samples = []
        for file in files:
            content = await file.read()
            samples.append(content)
        success = register_voice_profile(samples)
        if success:
            return {"success": True, "message": "Voice registered successfully."}
        else:
            return {"success": False, "error": "Could not register voice profile. Make sure files are valid WAVs."}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/voice-verify")
async def voice_verify(file: UploadFile = File(...)):
    """Verifies if the uploaded voice WAV sample belongs to Raj."""
    try:
        from agents.voice_auth import verify_speaker
        content = await file.read()
        is_raj, score = verify_speaker(content)
        return {"verified": bool(is_raj), "score": float(score)}
    except Exception as e:
        return {"verified": False, "error": str(e)}

@app.post("/api/face-register")
async def face_register():
    """Trigger LBPH face registration from webcam (30 samples). Run once to train Raj's face model."""
    try:
        from face_auth import register_face_from_webcam
        result = await asyncio.to_thread(register_face_from_webcam, 30)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/intruder-log")
async def intruder_log():
    """Returns list of intruder photo events for the BiometricsDashboard."""
    if not system_unlocked:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="System locked")
    try:
        entries = get_intruder_log()
        return {"success": True, "events": entries, "count": len(entries)}
    except Exception as e:
        return {"success": False, "error": str(e), "events": []}

@app.get("/api/emotion-state")
async def emotion_state():
    """Returns the latest detected emotion state for the frontend."""
    if not system_unlocked:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="System locked")
    try:
        state = get_current_emotion_state()
        return {"success": True, **state}
    except Exception as e:
        return {"success": False, "error": str(e), "emotion": "neutral"}

@app.get("/api/proactive-poll")
async def proactive_poll():
    """Polls for any pending proactive messages from JARVIS."""
    if not system_unlocked:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="System locked")
    try:
        msg = get_pending_proactive_message()
        if msg:
            return {"success": True, "has_message": True, **msg}
        return {"success": True, "has_message": False}
    except Exception as e:
        return {"success": False, "has_message": False, "error": str(e)}

@app.get("/api/github-stats")
async def github_stats_endpoint():
    """Returns live GitHub stats for the HUD widget."""
    if not system_unlocked:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="System locked")
    try:
        from agents.github_stats_agent import get_profile_stats, get_recent_activity
        stats_text = await asyncio.to_thread(get_profile_stats)
        activity_text = await asyncio.to_thread(get_recent_activity)
        return {"success": True, "stats": stats_text, "activity": activity_text}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/spotify-now-playing")
async def spotify_now_playing():
    """Returns the currently playing Spotify track."""
    if not system_unlocked:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="System locked")
    try:
        from agents.spotify_agent import get_now_playing
        result = await asyncio.to_thread(get_now_playing)
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not system_unlocked:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="System locked")
    # Create temp directory
    temp_dir = os.path.join(os.path.dirname(__file__), "temp")
    os.makedirs(temp_dir, exist_ok=True)
    file_path = os.path.join(temp_dir, file.filename)
    
    # Save the file
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
        
    try:
        import pypdf
        from groq import Groq
        
        # 1. Parse PDF text
        reader = pypdf.PdfReader(file_path)
        full_text = ""
        for page in reader.pages:
            full_text += page.extract_text() or ""
            
        # Clean up temp file
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # 2. Use Groq to analyze
        groq_key = os.getenv("GROQ_API_KEY", "")
        if not groq_key or groq_key == "your_groq_api_key_here":
            return JSONResponse(status_code=400, content={"success": False, "error": "Groq API key not found in environment."})
            
        client = Groq(api_key=groq_key)
        
        prompt = f"""
        Analyze the following text extracted from a PDF document:
        
        TEXT START:
        {full_text[:8000]}
        TEXT END:
        
        Task:
        1. Classify if this document is a Resume/CV or a general document (e.g. article, book, report).
        2. If it is a Resume/CV:
           - Calculate an ATS Compatibility Score out of 100 based on standard industry rules (keyword density, section completeness, readability, action verbs).
           - Provide a bulleted critique of formatting, strengths, weaknesses, and direct action items to improve it.
        3. If it is a general document:
           - Provide a concise executive summary of the content.
           - Detail 3-5 main key takeaways or insights.
           
        Format your response as a beautiful Markdown document. Make it highly professional and addressed to "Sir" (Raj).
        """
        
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are J.A.R.V.I.S., Raj's elite AI intelligence core. Address him as 'Sir' or 'Raj'."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        analysis = response.choices[0].message.content.strip()
        return {"success": True, "analysis": analysis}
        
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

@app.post("/api/analyze-gender")
async def analyze_gender(file: UploadFile = File(...)):
    """Analyze an uploaded image and detect if person is a boy or girl using Groq Vision."""
    if not system_unlocked:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="System locked")
    import base64

    allowed_types = ["image/jpeg", "image/png", "image/webp", "image/gif", "image/jpg"]
    content_type = file.content_type or "image/jpeg"
    if content_type not in allowed_types:
        return JSONResponse(status_code=400, content={"success": False, "error": "Please upload a valid image file (JPG, PNG, WEBP)."})

    try:
        image_bytes = await file.read()
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")

        groq_key = os.getenv("GROQ_API_KEY", "")
        if not groq_key or groq_key == "your_groq_api_key_here":
            return JSONResponse(status_code=400, content={"success": False, "error": "Groq API key not configured."})

        from groq import Groq
        client = Groq(api_key=groq_key)

        response = client.chat.completions.create(
            model="qwen/qwen3.6-27b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are J.A.R.V.I.S., Raj's elite AI intelligence core. "
                        "You analyze images with extreme precision. Address Raj as 'Sir'."
                    )
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{content_type};base64,{image_b64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": (
                                "Analyze this image in detail. "
                                "Identify what is depicted in the image. If there are people, specify gender or multiplicity. "
                                "If there are no people, classify the image category (e.g. Object, Scene, Animal, Text). "
                                "Respond ONLY with a JSON object (no markdown, no extra text) with these exact keys:\n"
                                "{\n"
                                "  \"gender\": \"Boy\", \"Girl\", \"Multiple\", \"Object\", \"Scene\", \"Text\", \"Animal\", or \"Unclear\" (representing the primary classification),\n"
                                "  \"confidence\": \"High\", \"Medium\", or \"Low\",\n"
                                "  \"count\": number of primary entities/people/objects detected (integer),\n"
                                "  \"description\": \"A brief 1-2 sentence JARVIS-style description for Sir/Raj detailing what the image contains\",\n"
                                "  \"details\": [\"list\", \"of\", \"visual\", \"cues\", \"objects\", \"or\", \"features\", \"identified\"]\n"
                                "}\n"
                            )
                        }
                    ]
                }
            ],
            temperature=0.1,
            max_tokens=400
        )

        raw = response.choices[0].message.content.strip()

        # Parse JSON response
        import json, re
        json_match = re.search(r'\{.*\}', raw, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
        else:
            result = {
                "gender": "Unclear",
                "confidence": "Low",
                "count": 0,
                "description": raw,
                "details": []
            }

        return {"success": True, "result": result}

    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
assets_dir = os.path.join(FRONTEND_DIST, "assets")
os.makedirs(assets_dir, exist_ok=True)
app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

@app.get("/")
async def serve_frontend():
    return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))

@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    file_path = os.path.join(FRONTEND_DIST, full_path)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))

# Default location if IP detection fails or returns wrong city
DEFAULT_CITY    = "Vadodara"
DEFAULT_REGION  = "Gujarat"
DEFAULT_COUNTRY = "India"

def _get_location():
    try:
        r = requests.get("http://ip-api.com/json/", timeout=3)
        d = r.json()
        city    = d.get("city", "").strip()
        region  = d.get("regionName", "").strip()
        country = d.get("country", "").strip()
        # Only use IP result if it returns a valid Indian city
        if city and country:
            return city, region, country
        return DEFAULT_CITY, DEFAULT_REGION, DEFAULT_COUNTRY
    except:
        return DEFAULT_CITY, DEFAULT_REGION, DEFAULT_COUNTRY

def _get_ist_time():
    utc_now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    return utc_now + datetime.timedelta(hours=5, minutes=30)

def _check_image_request(cmd: str):
    """
    Returns (image_type, query) or (None, None).
    image_type = 'search' for real photos, 'generate' for AI art.
    """
    cmd_lower = cmd.lower()

    # Real photo — open Google Images in new tab
    search_triggers = [
        "show image of", "show me image of", "show photo of", "show picture of",
        "show me photo of", "show me picture of", "image of", "photo of", "picture of",
    ]
    for t in search_triggers:
        if t in cmd_lower:
            query = cmd_lower.split(t)[-1].strip()
            if query:
                return ("search", query)

    # AI generation
    gen_triggers = [
        "generate image", "create image", "draw", "make image",
        "generate a picture", "create a picture"
    ]
    for t in gen_triggers:
        if t in cmd_lower:
            query = cmd_lower.split(t)[-1].strip()
            return ("generate", query if query else "abstract art")

    return (None, None)

def _google_image_url(query: str) -> str:
    return f"https://www.google.com/search?tbm=isch&q={query.replace(' ', '+')}"

def _pollinations_url(prompt: str) -> str:
    return f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}?width=800&height=600&nologo=true"

SOCKET_SECRET = os.getenv("SOCKET_SECRET", "jarvis-local-secret")

# System unlock state — managed by the React frontend connection
system_unlocked = False
frontend_sid = None

# Global command execution lock — prevents process_command and execute_global_command running simultaneously
_command_executing = False

# Per-session dismissed state: {sid: True/False}
# When True, Jarvis quietly ignores all commands until re-engaged.
_dismissed_sessions: dict = {}

# Rate limiting — max 1 command per 2 seconds per session
_rate_limit: dict = {}   # {sid: last_command_timestamp}
RATE_LIMIT_SECONDS = 2

def _is_rate_limited(sid: str) -> bool:
    now = time.time()
    last = _rate_limit.get(sid, 0)
    if now - last < RATE_LIMIT_SECONDS:
        return True
    _rate_limit[sid] = now
    return False

# Input validation constants
MAX_COMMAND_LENGTH = 500
BLOCKED_PATTERNS = [
    "rm -rf", "del /f", "format c", "drop table", "drop database",
    "os.system", "subprocess", "eval(", "exec(", "__import__",
    "javascript:", "file://", "data:text",
]

def _sanitize_command(command: str) -> tuple[bool, str]:
    """Returns (is_safe, cleaned_command). Rejects dangerous input."""
    if not command or not command.strip():
        return False, ""
    if len(command) > MAX_COMMAND_LENGTH:
        return False, ""
    cmd_lower = command.lower()
    for pattern in BLOCKED_PATTERNS:
        if pattern in cmd_lower:
            return False, ""
    cleaned = "".join(c for c in command if c.isprintable())
    return True, cleaned.strip()

async def play_welcome_greeting(sid):
    # Trigger welcome greeting for Raj
    ist = _get_ist_time()
    hour = ist.hour
    if   hour < 12: greeting = "Good morning, Sir."
    elif hour < 16: greeting = "Good afternoon, Sir."
    elif hour < 20: greeting = "Good evening, Sir."
    else:           greeting = "Good night, Sir."

    city, region, country = _get_location()
    time_str = ist.strftime("%I:%M %p")
    
    _dismissed_sessions[sid] = False   # default: active
    consent_message = (
        f"{greeting} Access granted. Welcome to the Raj Lab. It is {time_str} and you are in {city}, {country}. "
        f"JARVIS is ready for your instructions."
    )
    try:
        await sio.emit('system_log', {'time': ist.strftime("%H:%M:%S"), 'type': 'jarvis', 'message': consent_message}, room=sid)
        await sio.emit('activity_state', {'state': 'SPEAKING'}, room=sid)
        await asyncio.to_thread(speak_text, consent_message)
        await sio.emit('activity_state', {'state': 'LISTENING'}, room=sid)
    except Exception as e:
        print(f"[SECURITY ERROR] Welcome greeting exception: {e}")

@sio.event
async def connect(sid, environ, auth=None):
    global system_unlocked, frontend_sid
    token = (auth or {}).get("token", "")
    client_type = (auth or {}).get("client_type", "")
    
    if not token or not client_type:
        from urllib.parse import parse_qs
        query_string = environ.get("QUERY_STRING", "")
        params = parse_qs(query_string)
        if not token:
            token = params.get("token", [""])[0]
        if not client_type:
            client_type = params.get("client_type", [""])[0]

    if token != SOCKET_SECRET:
        print(f"Rejected unauthorized connection: {sid}")
        raise ConnectionRefusedError("Unauthorized")
    
    # Robust fallback: identify frontend by checking HTTP_ORIGIN or HTTP_REFERER if client_type is not provided
    if not client_type:
        origin = environ.get("HTTP_ORIGIN", "") or environ.get("HTTP_REFERER", "")
        if "localhost" in origin or "127.0.0.1" in origin or "jarvis.weblog" in origin:
            client_type = "frontend"
    
    print(f"Frontend connected: {sid} (Client type: {client_type})")
    
    if client_type == "frontend":
        system_unlocked = True
        frontend_sid = sid
        print(f"[SECURITY] Frontend connected: {sid}. System unlocked.")
        
        global auth_just_completed
        if auth_just_completed:
            auth_just_completed = False
            # Run welcome greeting as a background task to prevent blocking connection handshake
            asyncio.create_task(play_welcome_greeting(sid))
        else:
            print(f"[SECURITY] Reconnection/duplicate socket {sid} ignored for welcome greeting.")

@sio.event
async def authenticate(sid, data):
    print(f"Client {sid} authenticated via event (Extension connection).")

@sio.event
async def disconnect(sid):
    global system_unlocked, frontend_sid
    print(f"Frontend disconnected: {sid}")
    clear_session(sid)
    _rate_limit.pop(sid, None)
    _dismissed_sessions.pop(sid, None)
    if sid == frontend_sid:
        system_unlocked = False
        frontend_sid = None
        print("[SECURITY] Frontend disconnected. System locked.")

@sio.event
async def process_command(sid, data):
    global system_unlocked, _command_executing
    if not system_unlocked:
        print(f"[SECURITY] Blocked process_command from {sid} since system is locked.")
        return
    if _command_executing:
        print(f"[PROCESS CMD] Skipped — another command is already executing.")
        return
    _command_executing = True
    try:
        await _process_command_inner(sid, data)
    finally:
        _command_executing = False

async def _process_command_inner(sid, data):
    global system_unlocked
    raw_command = data.get('command', '') if isinstance(data, dict) else ''
    audio_b64 = data.get('audio', '') if isinstance(data, dict) else ''
    now = _get_ist_time().strftime("%H:%M:%S")

    # ── SPEAKER BIOMETRIC IDENTIFICATION ────────────────────────────────────
    # If audio bytes are sent with command, verify the speaker's voiceprint.
    # If it is NOT Raj, lock screen instantly for security breach.
    if audio_b64:
        import base64
        if "," in audio_b64:
            audio_b64 = audio_b64.split(",")[1]
        try:
            audio_bytes = base64.b64decode(audio_b64)
            from agents.voice_auth import verify_speaker
            is_raj, score = verify_speaker(audio_bytes)
            
            if not is_raj:
                lock_msg = f"⚠️ Intruder voice signature detected (Similarity: {score:.2f}). Locking system."
                await sio.emit('system_log', {'time': now, 'type': 'jarvis', 'message': lock_msg}, room=sid)
                await sio.emit('activity_state', {'state': 'SPEAKING'}, room=sid)
                await asyncio.to_thread(speak_text, "Security alert. Unauthorized voice detected. Locking the screen now.")
                # Capture intruder photo THEN lock screen
                lock_result, photo_path = await asyncio.to_thread(lock_screen_with_photo)
                photo_note = f" 📸 Photo saved at {photo_path}" if photo_path else ""
                await sio.emit('system_log', {'time': now, 'type': 'jarvis', 'message': lock_result + photo_note}, room=sid)
                await sio.emit('activity_state', {'state': 'STANDBY'}, room=sid)
                # Notify frontend to refresh intruder log
                await sio.emit('intruder_alert', {'photo_path': photo_path, 'score': score}, room=sid)
                return
            else:
                print(f"[VOICE AUTH] Raj verified successfully (Similarity: {score:.2f})")
        except Exception as e:
            print(f"[VOICE AUTH ERROR]: Verification failed, ignoring. {e}")

    # ── STOP/MUTE FAST-PATH ─────────────────────────────────────────────────
    if raw_command.lower().strip() in ["stop", "stop speaking", "be quiet", "shut up", "mute"]:
        interrupt()
        await sio.emit('system_log', {'time': now, 'type': 'jarvis', 'message': "Muted."}, room=sid)
        await sio.emit('activity_state', {'state': 'STANDBY'}, room=sid)
        return

    # Check for immediate COME BACK command to return to JARVIS page
    if raw_command.lower().strip() in ["come back", "go back to jarvis", "open jarvis page"]:
        await sio.emit('system_log', {'time': now, 'type': 'jarvis', 'message': "Coming back to my home screen, Raj."}, room=sid)
        await sio.emit('activity_state', {'state': 'SPEAKING'}, room=sid)
        if sys.platform == "darwin":
            script = """
            tell application "Google Chrome"
                activate
                set foundTab to false
                repeat with w in windows
                    set tabIndex to 1
                    repeat with t in tabs of w
                        if (URL of t contains "localhost:8000") or (URL of t contains "127.0.0.1:8000") or (URL of t contains "jarvis.weblog") then
                            set active tab index of w to tabIndex
                            set index of w to 1
                            set foundTab to true
                            exit repeat
                        end if
                        set tabIndex to tabIndex + 1
                    end repeat
                    if foundTab then exit repeat
                end repeat
            end tell
            """
            import subprocess
            subprocess.run(["osascript", "-e", script])
        await asyncio.to_thread(speak_text, "Welcome back, Raj.")
        await sio.emit('activity_state', {'state': 'STANDBY'}, room=sid)
        return

    # ── SECURITY FAST-PATH ─────────────────────────────────────────────────
    # Checked BEFORE sanitization, rate-limiting, or any routing.
    if is_intrusion_attempt(raw_command):
        if audio_b64:
            # If we reached here, the voice was verified as Raj's in the block above
            success_msg = "🔓 Welcome back, Sir. Raj Lab access granted."
            await sio.emit('system_log', {'time': now, 'type': 'jarvis', 'message': success_msg}, room=sid)
            await sio.emit('activity_state', {'state': 'SPEAKING'}, room=sid)
            await asyncio.to_thread(speak_text, "Access granted, Sir. Welcome to the Raj Lab.")
            await sio.emit('activity_state', {'state': 'STANDBY'}, room=sid)
            return
        else:
            # No voice biometrics provided (e.g. typed or text API call)
            lock_msg = "⚠️ Unverified access attempt. Locking the screen."
            await sio.emit('system_log', {'time': now, 'type': 'jarvis', 'message': lock_msg}, room=sid)
            await sio.emit('activity_state', {'state': 'SPEAKING'}, room=sid)
            await asyncio.to_thread(speak_text, "Security alert. Unverified access command. Locking the screen now.")
            lock_screen()
            await sio.emit('activity_state', {'state': 'STANDBY'}, room=sid)
            return

    # ── SHUTDOWN FAST-PATH ─────────────────────────────────────────────────
    if is_shutdown_command(raw_command):
        shutdown_msg = "Shutdown capability is disabled for safety, Sir."
        await sio.emit('system_log', {'time': now, 'type': 'jarvis', 'message': shutdown_msg}, room=sid)
        await sio.emit('activity_state', {'state': 'SPEAKING'}, room=sid)
        await asyncio.to_thread(speak_text, shutdown_msg)
        return

    # ── CLOSE ALL TABS FAST-PATH ────────────────────────────────────────────
    if is_close_all_tabs_command(raw_command):
        tabs_msg = "Closing all Chrome tabs now, Sir."
        await sio.emit('system_log', {'time': now, 'type': 'jarvis', 'message': tabs_msg}, room=sid)
        await sio.emit('activity_state', {'state': 'PROCESSING'}, room=sid)
        result = await asyncio.to_thread(close_all_chrome_tabs)
        await sio.emit('activity_state', {'state': 'SPEAKING'}, room=sid)
        await sio.emit('system_log', {'time': now, 'type': 'jarvis', 'message': result}, room=sid)
        await asyncio.to_thread(speak_text, result)
        await sio.emit('activity_state', {'state': 'STANDBY'}, room=sid)
        return

    is_safe, command = _sanitize_command(raw_command)
    if not is_safe:
        await sio.emit('system_log', {'time': _get_ist_time().strftime("%H:%M:%S"), 'type': 'jarvis', 'message': 'Raj, that command was blocked for security reasons.'}, room=sid)
        return

    # Interrupt any currently playing speech immediately
    interrupt()

    await sio.emit('system_log', {'time': now, 'type': 'user', 'message': command}, room=sid)

    # ── GREETING CONSENT GATE ──────────────────────────────────────────────
    # If Jarvis is in DISMISSED state, check if user wants to re-engage.
    cmd_lower = command.lower().strip()
    dismissed = _dismissed_sessions.get(sid, False)

    # Phrases that DISMISS Jarvis
    DISMISS_PHRASES = ["no", "not now", "no thanks", "don't need you", "go away",
                       "dismiss", "no help", "i'm fine", "im fine", "no need",
                       "not today", "exit", "disable", "not required"]
    # Phrases that WAKE Jarvis back up
    WAKE_PHRASES    = ["yes", "help", "yeah", "sure", "please", "i need you", "activate",
                       "i need help", "wake up", "wake", "jarvis", "okay", "ok"]

    if not dismissed:
        # Check if the user just answered the consent gate question
        if any(p == cmd_lower or cmd_lower.startswith(p) for p in DISMISS_PHRASES):
            _dismissed_sessions[sid] = True
            dismiss_msg = "Understood, Sir. I'll stand by quietly. Say 'Jarvis' or 'I need help' to wake me anytime."
            await sio.emit('system_log', {'time': now, 'type': 'jarvis', 'message': dismiss_msg}, room=sid)
            await sio.emit('activity_state', {'state': 'SPEAKING'}, room=sid)
            await asyncio.to_thread(speak_text, dismiss_msg)
            await sio.emit('activity_state', {'state': 'STANDBY'}, room=sid)
            return
    else:
        # In dismissed mode — only respond to wake phrases
        if any(p in cmd_lower for p in WAKE_PHRASES):
            _dismissed_sessions[sid] = False
            wake_msg = "JARVIS is back online, Sir. How can I help you?"
            await sio.emit('system_log', {'time': now, 'type': 'jarvis', 'message': wake_msg}, room=sid)
            await sio.emit('activity_state', {'state': 'SPEAKING'}, room=sid)
            await asyncio.to_thread(speak_text, wake_msg)
            await sio.emit('activity_state', {'state': 'LISTENING'}, room=sid)
            return
        else:
            # Silently ignore — Jarvis is dismissed
            return

    await sio.emit('activity_state', {'state': 'PROCESSING'}, room=sid)

    # --- Image check ---
    img_type, img_query = _check_image_request(command)
    if img_type == "search":
        url = _google_image_url(img_query)
        response = f"Raj, opening images of {img_query} in a new tab."
        await sio.emit('activity_state', {'state': 'SPEAKING'}, room=sid)
        await sio.emit('system_log', {'time': now, 'type': 'jarvis', 'message': response}, room=sid)
        await sio.emit('image_result', {'url': url, 'prompt': img_query}, room=sid)
        await asyncio.to_thread(speak_text, response)
        await sio.emit('activity_state', {'state': 'STANDBY'}, room=sid)
        return
    elif img_type == "generate":
        url = _pollinations_url(img_query)
        response = f"Raj, generating image of {img_query}."
        await sio.emit('activity_state', {'state': 'SPEAKING'}, room=sid)
        await sio.emit('system_log', {'time': now, 'type': 'jarvis', 'message': response}, room=sid)
        await sio.emit('image_result', {'url': url, 'prompt': img_query}, room=sid)
        await asyncio.to_thread(speak_text, response)
        await sio.emit('activity_state', {'state': 'STANDBY'}, room=sid)
        return

    # --- Heartbeat check ---
    if any(w in command.lower() for w in ["heartbeat", "heart rate", "heart beat",
                                           "pulse", "bpm", "check my heart"]):
        await sio.emit('activity_state', {'state': 'PROCESSING'}, room=sid)
        await sio.emit('system_log', {'time': now, 'type': 'jarvis',
                        'message': 'Raj, starting heart rate scan. Look at the camera and stay still for 15 seconds.'}, room=sid)
        await asyncio.to_thread(speak_text, 'Starting heart rate scan. Look at the camera and stay still, Raj.')
        heart_response = await asyncio.to_thread(measure_heart_rate)
        await sio.emit('activity_state', {'state': 'SPEAKING'}, room=sid)
        await sio.emit('system_log', {'time': now, 'type': 'jarvis', 'message': heart_response}, room=sid)
        await asyncio.to_thread(speak_text, heart_response)
        await sio.emit('activity_state', {'state': 'STANDBY'}, room=sid)
        return

    # --- Website builder check ---
    if is_build_request(command):
        build_prompt = extract_build_prompt(command)
        await sio.emit('activity_state', {'state': 'PROCESSING'}, room=sid)
        await sio.emit('system_log', {'time': now, 'type': 'jarvis', 'message': f"Raj, building your website now. This may take a few seconds..."}, room=sid)
        await asyncio.to_thread(speak_text, "Building your website now, Raj. Please wait a moment.")
        build_response = await asyncio.to_thread(build_website, build_prompt)
        await sio.emit('activity_state', {'state': 'SPEAKING'}, room=sid)
        await sio.emit('system_log', {'time': now, 'type': 'jarvis', 'message': build_response}, room=sid)
        await asyncio.to_thread(speak_text, build_response)
        await sio.emit('activity_state', {'state': 'STANDBY'}, room=sid)
        return

    # --- Live data check (weather, stocks, cricket) BEFORE routing ---
    live_response = await asyncio.to_thread(handle_live_query, command)
    if live_response:
        await sio.emit('activity_state', {'state': 'SPEAKING'}, room=sid)
        await sio.emit('system_log', {'time': now, 'type': 'jarvis', 'message': live_response}, room=sid)
        await asyncio.to_thread(speak_text, live_response)
        await sio.emit('activity_state', {'state': 'STANDBY'}, room=sid)
        return

    route_info = route_command(command)
    agent_type = route_info.get("agent")
    agent_name_upper = agent_type.upper() if agent_type else "UNKNOWN"
    await sio.emit('system_log', {'time': now, 'type': 'system', 'message': f"ROUTING TO {agent_name_upper} AGENT"}, room=sid)

    response = ""
    event_name = None
    event_data = None
    try:
        if agent_type == "system":       response = await asyncio.to_thread(execute_system_command, command)
        elif agent_type == "web":
            result = await asyncio.to_thread(web_search, command)
            if isinstance(result, tuple):
                response, tab_url = result
                if tab_url:
                    event_name = "open_tab"
                    event_data = {"url": tab_url}
            else:
                response = result
        elif agent_type == "automation":
            result = await asyncio.to_thread(execute_automation, command)
            if isinstance(result, tuple):
                if len(result) == 3:
                    response, event_name, event_data = result
                elif len(result) == 2:
                    response, tab_url = result
                    if tab_url:
                        event_name = "open_tab"
                        event_data = {"url": tab_url}
            else:
                response = result
        elif agent_type == "crew":
            topic = command.replace("crew", "").replace("newsletter", "").replace("tech digest", "").replace("weekly digest", "").strip()
            if not topic:
                topic = "latest AI and technology news"
            response = run_tech_digest_crew(topic)
        # ── NEW AGENTS ────────────────────────────────────────────────────────
        elif agent_type == "screen":
            response = await asyncio.to_thread(analyze_screen, command)
        elif agent_type == "emotion":
            response = await asyncio.to_thread(emotion_check_response, command)
            # Also emit emotion state for the HUD
            emotion_state_data = get_current_emotion_state()
            await sio.emit('emotion_update', emotion_state_data, room=sid)
        elif agent_type == "gmail":
            response = await asyncio.to_thread(handle_gmail_command, command)
        elif agent_type == "calendar":
            response = await asyncio.to_thread(handle_calendar_command, command)
        elif agent_type == "spotify":
            response = await asyncio.to_thread(handle_spotify_command, command)
            # Emit updated now-playing for the Spotify widget
            await sio.emit('spotify_update', {'command': command}, room=sid)
        elif agent_type == "translation":
            response = await asyncio.to_thread(translate_command, command)
        elif agent_type == "github":
            response = await asyncio.to_thread(handle_github_command, command)
        elif agent_type == "proactive":
            response = await asyncio.to_thread(trigger_morning_briefing)
        else:
            response = chat_response(command, sid)
    except Exception as e:
        response = f"Raj, I encountered a critical error: {e}"

    await sio.emit('activity_state', {'state': 'SPEAKING'}, room=sid)
    await sio.emit('system_log', {'time': now, 'type': 'jarvis', 'message': response}, room=sid)
    if event_name:
        await sio.emit(event_name, event_data)
    # Speak and update UI simultaneously
    await asyncio.gather(
        asyncio.to_thread(speak_text, response),
    )
    await sio.emit('activity_state', {'state': 'STANDBY'}, room=sid)

if __name__ == "__main__":
    print("\n" + "="*50)
    print("  JARVIS is running at: http://127.0.0.1:8000")
    print("  Open this URL in Chrome")
    print("="*50 + "\n")
    uvicorn.run("main:socket_app", host="0.0.0.0", port=8000, reload=False)
