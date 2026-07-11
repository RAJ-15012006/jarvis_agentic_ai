"""
face_auth.py — JARVIS Dual Biometric Face Authentication
=========================================================
Upgraded from basic Haar Cascade detection to dual-layer verification:

Layer 1: Haar Cascade — detects ANY face (fast gate-keep)
Layer 2: LBPH Recognizer — verifies the face is RAJ's (identity check)

If no LBPH model is trained yet, falls back to Layer 1 only (open access mode).
Registration runs via backend/register_face.py.
"""

import cv2
import time
import os
import numpy as np

CASCADE = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"

# Directory for biometric data
BIOMETRIC_DIR = os.path.join(os.path.dirname(__file__), "agents", "face_data")
os.makedirs(BIOMETRIC_DIR, exist_ok=True)

LBPH_MODEL_PATH = os.path.join(BIOMETRIC_DIR, "lbph_face_model.xml")
RAJ_LABEL = 0  # Label 0 = Raj in the LBPH model

# Confidence threshold — LOWER is more similar in LBPH
# A score below this value means "recognized as Raj"
LBPH_CONFIDENCE_THRESHOLD = 70.0


# ---------------------------------------------------------------------------
# Training / Registration
# ---------------------------------------------------------------------------

def train_face_model(images: list, labels: list) -> bool:
    """
    Train the LBPH model on a list of grayscale face images.
    images: list of numpy arrays (grayscale face crops)
    labels: list of int labels (0 = Raj)
    Returns True if training was successful.
    """
    try:
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        recognizer.train(images, np.array(labels))
        recognizer.write(LBPH_MODEL_PATH)
        print(f"[FACE AUTH] LBPH model trained and saved to {LBPH_MODEL_PATH}")
        return True
    except Exception as e:
        print(f"[FACE AUTH] Training failed: {e}")
        return False


def register_face_from_webcam(num_samples: int = 30) -> dict:
    """
    Capture num_samples face samples from the webcam and train LBPH model.
    Called by the API endpoint /api/face-register.
    Returns {"success": bool, "samples_captured": int}
    """
    detector = cv2.CascadeClassifier(CASCADE)
    cam = cv2.VideoCapture(0)

    if not cam.isOpened():
        return {"success": False, "error": "Could not open webcam."}

    face_images = []
    labels = []
    captured = 0
    start = time.time()

    print(f"[FACE AUTH] Starting registration — capturing {num_samples} face samples for Raj...")

    while captured < num_samples and time.time() - start < 60:
        ret, frame = cam.read()
        if not ret:
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

        for (x, y, w, h) in faces:
            face_roi = gray[y:y + h, x:x + w]
            face_resized = cv2.resize(face_roi, (200, 200))
            face_images.append(face_resized)
            labels.append(RAJ_LABEL)
            captured += 1

            try:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, f"Capturing: {captured}/{num_samples}",
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                cv2.imshow("JARVIS — Face Registration", frame)
                cv2.waitKey(100)
            except Exception:
                pass

            if captured >= num_samples:
                break

        time.sleep(0.05)

    cam.release()
    try:
        cv2.destroyAllWindows()
    except Exception:
        pass

    if captured < 5:
        return {"success": False, "error": f"Only {captured} samples captured — need at least 5."}

    success = train_face_model(face_images, labels)
    return {"success": success, "samples_captured": captured}


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

def verify_face() -> dict:
    """
    Dual-layer face verification:
    1. Haar Cascade detects faces
    2. LBPH Recognizer identifies if it's Raj

    Returns {"verified": bool, "confidence": float, "mode": str}
    """
    detector = cv2.CascadeClassifier(CASCADE)
    cam = cv2.VideoCapture(0)

    if not cam.isOpened():
        print("[FACE AUTH] Warning: Could not open webcam — auto-approving.")
        return {"verified": True, "confidence": 0.0, "mode": "webcam_unavailable"}

    # Load LBPH model if available
    recognizer = None
    use_lbph = False
    if os.path.exists(LBPH_MODEL_PATH):
        try:
            recognizer = cv2.face.LBPHFaceRecognizer_create()
            recognizer.read(LBPH_MODEL_PATH)
            use_lbph = True
            print("[FACE AUTH] LBPH model loaded — running dual biometric check.")
        except Exception as e:
            print(f"[FACE AUTH] Could not load LBPH model ({e}), falling back to detection only.")

    if not use_lbph:
        print("[FACE AUTH] Running in 'Anyone Access' mode (no LBPH model trained yet).")

    start_time = time.time()
    SCAN_TIMEOUT = 15  # seconds
    best_confidence = 999.0
    raj_detected = False

    while time.time() - start_time < SCAN_TIMEOUT:
        ret, frame = cam.read()
        if not ret:
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

        for (x, y, w, h) in faces:
            face_roi = gray[y:y + h, x:x + w]
            face_resized = cv2.resize(face_roi, (200, 200))

            if use_lbph:
                label, confidence = recognizer.predict(face_resized)
                is_raj = (label == RAJ_LABEL and confidence < LBPH_CONFIDENCE_THRESHOLD)

                if confidence < best_confidence:
                    best_confidence = confidence

                color = (0, 255, 0) if is_raj else (0, 0, 255)
                status_text = f"RAJ — {confidence:.1f}" if is_raj else f"UNKNOWN — {confidence:.1f}"

                try:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                    cv2.putText(frame, status_text, (x, y - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                    cv2.imshow("JARVIS — Biometric Auth", frame)
                    cv2.waitKey(100)
                except Exception:
                    pass

                if is_raj:
                    raj_detected = True
                    break
            else:
                # No LBPH — any face passes
                raj_detected = True
                best_confidence = 0.0
                try:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.putText(frame, "Identity Verified", (x, y - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    cv2.imshow("JARVIS — Biometric Auth", frame)
                    cv2.waitKey(1000)
                except Exception:
                    pass

        if raj_detected:
            break

        try:
            cv2.putText(frame, "Scanning for Raj...", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            cv2.imshow("JARVIS — Biometric Auth", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        except Exception:
            time.sleep(0.05)

    cam.release()
    try:
        cv2.destroyAllWindows()
    except Exception:
        pass

    mode = "lbph" if use_lbph else "detection_only"
    confidence_score = float(best_confidence) if best_confidence < 999.0 else 0.0

    return {
        "verified": raj_detected,
        "confidence": confidence_score,
        "mode": mode,
        "threshold": LBPH_CONFIDENCE_THRESHOLD if use_lbph else None,
    }


def run_face_auth() -> dict:
    """Main entry point — runs dual-layer verification and returns result."""
    result = verify_face()
    return {
        "verified": result["verified"],
        "confidence": result.get("confidence", 0.0),
        "mode": result.get("mode", "unknown"),
        "attempts_left": 3,
        "locked": False,
    }
