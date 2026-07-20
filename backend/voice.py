import asyncio
import os
import glob
import tempfile
import time
import edge_tts
import pygame
import subprocess
import sys

VOICE = "en-GB-RyanNeural"
RATE  = "+15%"   # slightly faster for snappier feel
PITCH = "-5Hz"

def set_voice(gender: str):
    global VOICE
    if gender.lower() == "female":
        VOICE = "en-GB-SoniaNeural"
    else:
        VOICE = "en-GB-RyanNeural"

# Global interrupt flag and speech session tracking
_stop_speaking = False
_current_audio_process = None
_current_speech_id = 0
_speaking_flag = False

# Keep pygame mixer alive — avoid init/quit overhead on every call
_mixer_ready = False

def _ensure_mixer():
    global _mixer_ready
    if not _mixer_ready:
        pygame.mixer.pre_init(44100, -16, 2, 512)  # smaller buffer = less latency
        pygame.mixer.init()
        _mixer_ready = True

def is_speaking() -> bool:
    global _speaking_flag, _current_audio_process
    if _speaking_flag:
        return True
    if sys.platform == "darwin":
        return _current_audio_process is not None and _current_audio_process.poll() is None
    else:
        try:
            import pygame
            return pygame.mixer.get_init() and pygame.mixer.music.get_busy()
        except Exception:
            return False

def interrupt():
    global _stop_speaking, _current_audio_process, _current_speech_id, _speaking_flag
    _stop_speaking = True
    _speaking_flag = False
    _current_speech_id += 1
    try:
        if _current_audio_process:
            _current_audio_process.terminate()
            _current_audio_process = None
    except Exception:
        pass
    if sys.platform == "darwin":
        try:
            subprocess.run(["pkill", "afplay"], capture_output=True)
        except Exception:
            pass
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
    global _stop_speaking, _current_speech_id, _speaking_flag
    _stop_speaking = False
    _speaking_flag = True
    _current_speech_id += 1
    my_speech_id = _current_speech_id
    _purge_stale_tmp()
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            future = asyncio.run_coroutine_threadsafe(_speak_async(text, my_speech_id), loop)
            future.result()
            return
    except RuntimeError:
        pass
    try:
        asyncio.run(_speak_async(text, my_speech_id))
    except RuntimeError:
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            pool.submit(asyncio.run, _speak_async(text, my_speech_id))

async def _speak_async(text: str, my_speech_id: int):
    global _stop_speaking, _current_audio_process, _current_speech_id, _speaking_flag
    _speaking_flag = True
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".mp3", dir=TMP_DIR)
    os.close(tmp_fd)
    try:
        # Generate TTS audio
        communicate = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH)
        await communicate.save(tmp_path)

        if _stop_speaking or _current_speech_id != my_speech_id:
            return

        if sys.platform == "darwin":
            # Play using native macOS afplay to avoid Pygame conflicts & segfaults
            # Kill any existing afplay processes first to ensure no overlap
            try:
                subprocess.run(["pkill", "afplay"], capture_output=True)
            except Exception:
                pass
            
            audio_process = subprocess.Popen(["afplay", tmp_path])
            _current_audio_process = audio_process
            while audio_process.poll() is None:
                if _stop_speaking or _current_speech_id != my_speech_id:
                    try:
                        audio_process.terminate()
                    except Exception:
                        pass
                    break
                await asyncio.sleep(0.05)
            if _current_audio_process == audio_process:
                _current_audio_process = None
        else:
            # Play with persistent mixer on other platforms
            _ensure_mixer()
            pygame.mixer.music.load(tmp_path)
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():
                if _stop_speaking or _current_speech_id != my_speech_id:
                    pygame.mixer.music.stop()
                    break
                await asyncio.sleep(0.05)

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
        _speaking_flag = False
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass
