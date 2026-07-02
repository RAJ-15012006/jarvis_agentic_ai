import asyncio
import os
import glob
import tempfile
import time
import edge_tts
import pygame

VOICE = "en-GB-RyanNeural"
RATE  = "+15%"   # slightly faster for snappier feel
PITCH = "-5Hz"

def set_voice(gender: str):
    global VOICE
    if gender.lower() == "female":
        VOICE = "en-GB-SoniaNeural"
    else:
        VOICE = "en-GB-RyanNeural"

# Global interrupt flag
_stop_speaking = False

# Keep pygame mixer alive — avoid init/quit overhead on every call
_mixer_ready = False

def _ensure_mixer():
    global _mixer_ready
    if not _mixer_ready:
        pygame.mixer.pre_init(44100, -16, 2, 512)  # smaller buffer = less latency
        pygame.mixer.init()
        _mixer_ready = True

def interrupt():
    global _stop_speaking
    _stop_speaking = True
    try:
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
    except Exception:
        pass

TMP_DIR = os.path.join(tempfile.gettempdir(), "jarvis_tts")
os.makedirs(TMP_DIR, exist_ok=True)

def _purge_stale_tmp():
    try:
        now = time.time()
        for f in glob.glob(os.path.join(TMP_DIR, "*.mp3")):
            if now - os.path.getmtime(f) > 60:
                try: os.remove(f)
                except: pass
    except Exception:
        pass

def speak_text(text: str):
    global _stop_speaking
    _stop_speaking = False
    _purge_stale_tmp()
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            future = asyncio.run_coroutine_threadsafe(_speak_async(text), loop)
            future.result()
            return
    except RuntimeError:
        pass
    try:
        asyncio.run(_speak_async(text))
    except RuntimeError:
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            pool.submit(asyncio.run, _speak_async(text))

async def _speak_async(text: str):
    global _stop_speaking
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".mp3", dir=TMP_DIR)
    os.close(tmp_fd)
    try:
        # Generate TTS audio
        communicate = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH)
        await communicate.save(tmp_path)

        if _stop_speaking:
            return

        # Play with persistent mixer — no init/quit overhead
        _ensure_mixer()
        pygame.mixer.music.load(tmp_path)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            if _stop_speaking:
                pygame.mixer.music.stop()
                break
            await asyncio.sleep(0.05)  # check every 50ms instead of 100ms

        pygame.mixer.music.unload()

    except Exception as e:
        print(f"[JARVIS AUDIO ERROR]: {e}")
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty('rate', 180)
            engine.say(text)
            engine.runAndWait()
        except Exception:
            print(f"[JARVIS AUDIO]: {text}")
    finally:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass
