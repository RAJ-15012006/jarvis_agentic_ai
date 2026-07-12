"""
global_voice_listener.py — Standalone Global Microphone Voice Listener
========================================================================
Runs in a separate OS process to avoid blocking the FastAPI uvicorn server.
Listens to the default system microphone using sounddevice InputStream,
detects speech dynamically via amplitude threshold, transcribes complete
phrases, and posts them to the local JARVIS API.
"""

import time
import os
import requests
import sys
import queue
import numpy as np
import sounddevice as sd
import soundfile as sf
import speech_recognition as sr
import tempfile
import threading

# ── Configuration ────────────────────────────────────────────────────────────
API_URL = "http://127.0.0.1:8000/api/voice-command"
SAMPLE_RATE = 16000

# Voice Activity Detection (VAD) parameters
SILENCE_THRESHOLD = 800  # Amplitude threshold (lower = more sensitive)
SILENCE_DURATION = 1.0   # Seconds of silence to trigger end of phrase
MAX_PHRASE_DURATION = 8.0 # Max duration to prevent infinite recording

def run_listener():
    audio_queue = queue.Queue()
    
    # State variables for VAD
    state = {
        "recording": False,
        "frames": [],
        "silence_counter": 0,
        "total_frames": 0
    }
    
    # Minimum frames of silence needed to trigger end of phrase
    # (each callback block is 512 frames @ 16kHz = 0.032 seconds)
    block_duration = 512 / SAMPLE_RATE
    silence_limit = int(SILENCE_DURATION / block_duration)
    max_frame_limit = int(MAX_PHRASE_DURATION / block_duration)

    def audio_callback(indata, frames_count, time_info, status):
        """This is called for each audio block by sounddevice."""
        if status:
            print(f"[VOICE LISTENER] InputStream status: {status}", file=sys.stderr)
            
        data = indata.copy().flatten()
        max_val = np.max(np.abs(data))
        
        if not state["recording"]:
            # If sound level is above threshold, start recording a phrase
            if max_val > SILENCE_THRESHOLD:
                state["recording"] = True
                state["frames"] = [data]
                state["silence_counter"] = 0
                state["total_frames"] = 1
        else:
            state["frames"].append(data)
            state["total_frames"] += 1
            
            # Check if current frame is silent
            if max_val < SILENCE_THRESHOLD:
                state["silence_counter"] += 1
            else:
                state["silence_counter"] = 0
                
            # Trigger end of phrase if silent for too long, or reached max duration
            if state["silence_counter"] >= silence_limit or state["total_frames"] >= max_frame_limit:
                # Compile complete phrase
                phrase_audio = np.concatenate(state["frames"])
                audio_queue.put(phrase_audio)
                # Reset state
                state["recording"] = False
                state["frames"] = []
                state["silence_counter"] = 0
                state["total_frames"] = 0

    def transcriber_worker():
        r = sr.Recognizer()
        print("[VOICE LISTENER] Global VAD transcription thread active...")
        while True:
            try:
                recording = audio_queue.get()
                
                temp_dir = tempfile.gettempdir()
                temp_path = os.path.join(temp_dir, f"jarvis_voice_phrase_{int(time.time())}.wav")
                sf.write(temp_path, recording, SAMPLE_RATE)

                with sr.AudioFile(temp_path) as source:
                    audio_data = r.record(source)

                try:
                    text = r.recognize_google(audio_data).lower().strip()
                    if text:
                        cleaned = text.replace("hey jarvis", "").replace("jarvis", "").strip()
                        if cleaned:
                            print(f"[VOICE LISTENER] Heard: '{cleaned}' (Posting to server...)")
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
                    audio_queue.task_done()
            except Exception as e:
                print(f"[VOICE LISTENER] Transcribing loop error: {e}")
                time.sleep(1)

    # Start transcriber worker
    threading.Thread(target=transcriber_worker, daemon=True).start()

    print("[VOICE LISTENER] Listening for speech dynamically using sounddevice InputStream...")
    try:
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='int16', 
                            blocksize=512, callback=audio_callback):
            while True:
                time.sleep(1)
    except Exception as e:
        print(f"[VOICE LISTENER] InputStream failed to start: {e}")

if __name__ == "__main__":
    # Wait briefly for main server to boot up first
    time.sleep(3)
    run_listener()
