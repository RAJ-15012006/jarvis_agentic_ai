"""
global_voice_listener.py — Standalone Global Microphone Voice Listener
========================================================================
Runs in a separate OS process to avoid blocking the FastAPI uvicorn server.
Listens to the default system microphone, transcribes speech, and posts
commands to the local JARVIS API.
"""

import time
import os
import requests

# ── Configuration ────────────────────────────────────────────────────────────
API_URL = "http://127.0.0.1:8000/api/voice-command"
SAMPLE_RATE = 16000
CHUNK_DURATION = 3.5  # Listen in 3.5-second windows

def run_listener():
    # Delay imports until runtime to verify packages
    import sounddevice as sd
    import soundfile as sf
    import speech_recognition as sr
    import numpy as np
    import tempfile
    
    r = sr.Recognizer()
    print("[VOICE LISTENER] Continuous global microphone listener active...")
    
    while True:
        try:
            # Record audio block from microphone
            recording = sd.rec(
                int(CHUNK_DURATION * SAMPLE_RATE),
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype='int16'
            )
            sd.wait()
            
            # Simple volume threshold (Voice Activity Detection fallback)
            max_val = np.max(np.abs(recording))
            if max_val < 900:  # Adjust if the room is noisy or microphone is quiet
                continue
                
            # Save chunk temporarily
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, f"jarvis_voice_chunk_{int(time.time())}.wav")
            sf.write(temp_path, recording, SAMPLE_RATE)
            
            with sr.AudioFile(temp_path) as source:
                audio_data = r.record(source)
                
            try:
                # Transcribe using Google Speech Recognition
                text = r.recognize_google(audio_data).lower().strip()
                if text:
                    cleaned = text.replace("hey jarvis", "").replace("jarvis", "").strip()
                    if cleaned:
                        print(f"[VOICE LISTENER] Heard: '{cleaned}' (Posting to server...)")
                        # Send command to local FastAPI server
                        resp = requests.post(API_URL, json={"command": cleaned}, timeout=5)
                        print(f"[VOICE LISTENER] Server response: {resp.status_code}")
            except sr.UnknownValueError:
                pass
            except Exception as e:
                print(f"[VOICE LISTENER] Recognition error: {e}")
            finally:
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except:
                        pass
        except Exception as e:
            print(f"[VOICE LISTENER] Loop error: {e}")
            time.sleep(2)

if __name__ == "__main__":
    # Wait briefly for main server to boot up first
    time.sleep(3)
    run_listener()
