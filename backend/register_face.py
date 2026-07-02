"""
Run this ONCE to register Raj's face.
Usage: python register_face.py
"""
import cv2
import numpy as np
import os

FACE_DIR   = os.path.join(os.path.dirname(__file__), "face_data")
MODEL_PATH = os.path.join(FACE_DIR, "face_model.yml")
CASCADE    = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"

os.makedirs(FACE_DIR, exist_ok=True)

PHASES = [
    ("Look STRAIGHT at camera",       0),
    ("Tilt slightly LEFT",             1),
    ("Tilt slightly RIGHT",            2),
    ("Tilt slightly UP",               3),
    ("Tilt slightly DOWN",             4),
]
SAMPLES_PER_PHASE = 100  # 100 x 5 phases = 500 total samples

def register():
    detector = cv2.CascadeClassifier(CASCADE)
    cam      = cv2.VideoCapture(0)
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    all_samples = []
    all_labels  = []

    for phase_msg, phase_idx in PHASES:
        count = 0
        print(f"\n>>> Phase {phase_idx+1}/5: {phase_msg} — Press SPACE to start")

        # Wait for spacebar
        while True:
            ret, frame = cam.read()
            if not ret: continue
            cv2.putText(frame, f"{phase_msg}", (10, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
            cv2.putText(frame, "Press SPACE to start capturing", (10, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
            cv2.imshow("JARVIS - Face Registration", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord(' '): break
            if key == ord('q'):
                cam.release(); cv2.destroyAllWindows(); return

        # Capture samples for this phase
        while count < SAMPLES_PER_PHASE:
            ret, frame = cam.read()
            if not ret: continue

            gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # Apply histogram equalization for better lighting robustness
            gray  = cv2.equalizeHist(gray)
            faces = detector.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(80, 80))

            for (x, y, w, h) in faces:
                face_roi = cv2.resize(gray[y:y+h, x:x+w], (200, 200))
                all_samples.append(face_roi)
                all_labels.append(0)
                count += 1
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 180), 2)

            cv2.putText(frame, f"{phase_msg}  [{count}/{SAMPLES_PER_PHASE}]", (10, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 180), 2)
            cv2.imshow("JARVIS - Face Registration", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                cam.release(); cv2.destroyAllWindows(); return

        print(f"    Phase {phase_idx+1} done — {count} samples captured")

    cam.release()
    cv2.destroyAllWindows()

    if len(all_samples) < 50:
        print("Not enough samples. Please try again.")
        return

    print(f"\nTraining model on {len(all_samples)} samples...")
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train(all_samples, np.array(all_labels))
    recognizer.save(MODEL_PATH)
    print(f"✅ Face registered! Model saved to {MODEL_PATH}")
    print("Start JARVIS — it will now recognize your face reliably.")

if __name__ == "__main__":
    register()
