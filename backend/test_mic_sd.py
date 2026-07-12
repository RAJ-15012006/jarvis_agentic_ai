import sounddevice as sd
import soundfile as sf
import speech_recognition as sr
import numpy as np
import tempfile
import os

def test_mic():
    fs = 16000  # Sample rate
    seconds = 3  # Duration
    print("Recording 3 seconds...")
    myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()  # Wait until recording is finished
    print("Finished recording. Recognizing...")
    
    # Save to temp WAV file
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, "test_mic.wav")
    sf.write(temp_path, myrecording, fs)
    
    r = sr.Recognizer()
    with sr.AudioFile(temp_path) as source:
        audio_data = r.record(source)
        try:
            text = r.recognize_google(audio_data)
            print("Google Speech Recognition saw:", text)
        except sr.UnknownValueError:
            print("Google Speech Recognition could not understand audio")
        except sr.RequestError as e:
            print("Could not request results; {0}".format(e))
            
    if os.path.exists(temp_path):
        os.remove(temp_path)

if __name__ == "__main__":
    test_mic()
