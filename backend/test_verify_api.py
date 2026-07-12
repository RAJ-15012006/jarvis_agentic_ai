import requests
import io
import scipy.io.wavfile as wav
import numpy as np

def test_verify_endpoint():
    url = "http://127.0.0.1:8000/api/voice-verify"
    
    # Create a dummy 1-second 16000Hz mono WAV in memory
    fs = 16000
    t = np.linspace(0, 1, fs)
    data = np.sin(2 * np.pi * 440 * t)  # 440Hz sine wave
    data = (data * 32767).astype(np.int16)
    
    wav_io = io.BytesIO()
    wav.write(wav_io, fs, data)
    wav_bytes = wav_io.getvalue()
    
    # Send POST request
    files = {'file': ('verify.wav', wav_bytes, 'audio/wav')}
    print(f"Sending request to {url}...")
    try:
        resp = requests.post(url, files=files)
        print("Status code:", resp.status_code)
        print("Headers:", resp.headers)
        print("Content:", resp.text)
    except Exception as e:
        print("Error sending request:", e)

if __name__ == "__main__":
    test_verify_endpoint()
