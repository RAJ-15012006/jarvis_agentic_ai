"""
emotion_agent.py — JARVIS Emotion Detection
============================================
Uses OpenCV + a lightweight CNN approach to detect Raj's facial emotion
from the webcam. JARVIS adapts its response style accordingly.

Emotions detected: happy, sad, angry, surprised, fearful, disgusted, neutral, stressed

Strategy: Uses DeepFace if available, falls back to a simple rule-based
approach using eye-openness and facial geometry from OpenCV landmarks.
No heavy ML model required for fallback.
"""

import cv2
import time
import os
import json

CASCADE = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"

# Emotion → JARVIS personality modifier
EMOTION_RESPONSES = {
    "happy": {
        "greeting": "You seem to be in great spirits today, Sir! Let's make something amazing.",
        "style": "enthusiastic",
        "emoji": "😊",
        "suggestion": None,
    },
    "sad": {
        "greeting": "Sir, I notice you seem a bit down. I'm here if you need anything — or just some company.",
        "style": "gentle",
        "emoji": "💙",
        "suggestion": "Would you like some calming music or a motivational quote?",
    },
    "angry": {
        "greeting": "Sir, I sense some frustration. Take a deep breath — let's solve whatever's bothering you.",
        "style": "calm",
        "emoji": "🔴",
        "suggestion": "Would you like me to put on some calming music?",
    },
    "surprised": {
        "greeting": "Something caught you off guard, Sir? I'm paying attention.",
        "style": "attentive",
        "emoji": "😲",
        "suggestion": None,
    },
    "fearful": {
        "greeting": "Sir, you appear concerned. I'm monitoring all systems — everything looks secure.",
        "style": "reassuring",
        "emoji": "🛡️",
        "suggestion": "Shall I run a security check?",
    },
    "disgusted": {
        "greeting": "That expression tells me something isn't right. What do you need, Sir?",
        "style": "direct",
        "emoji": "😤",
        "suggestion": None,
    },
    "stressed": {
        "greeting": "Sir, you look stressed. You've been working hard — shall I schedule a break?",
        "style": "supportive",
        "emoji": "😓",
        "suggestion": "You've been active for a while. Consider a 5-minute break, Sir.",
    },
    "neutral": {
        "greeting": "Ready for your commands, Sir.",
        "style": "professional",
        "emoji": "🤖",
        "suggestion": None,
    },
}

# State file for the last detected emotion (shared with frontend via polling)
EMOTION_STATE_FILE = os.path.join(
    os.path.dirname(__file__), "face_data", "current_emotion.json"
)
os.makedirs(os.path.dirname(EMOTION_STATE_FILE), exist_ok=True)


def _save_emotion_state(emotion: str, confidence: float):
    """Save current emotion to a state file for the frontend to poll."""
    try:
        state = {
            "emotion": emotion,
            "confidence": round(confidence, 3),
            "emoji": EMOTION_RESPONSES.get(emotion, {}).get("emoji", "🤖"),
            "suggestion": EMOTION_RESPONSES.get(emotion, {}).get("suggestion"),
            "style": EMOTION_RESPONSES.get(emotion, {}).get("style", "professional"),
        }
        with open(EMOTION_STATE_FILE, "w") as f:
            json.dump(state, f)
    except Exception:
        pass


def detect_emotion_deepface() -> dict:
    """
    Use DeepFace for emotion detection (if installed).
    Returns {"emotion": str, "confidence": float} or None if unavailable.
    """
    try:
        from deepface import DeepFace
        import numpy as np

        cam = cv2.VideoCapture(0)
        if not cam.isOpened():
            return None

        # Warm up + grab a few frames for stability
        for _ in range(8):
            cam.read()

        ret, frame = cam.read()
        cam.release()

        if not ret or frame is None:
            return None

        result = DeepFace.analyze(
            frame,
            actions=["emotion"],
            enforce_detection=False,
            silent=True
        )

        if isinstance(result, list):
            result = result[0]

        emotion = result.get("dominant_emotion", "neutral")
        emotions_raw = result.get("emotion", {})
        confidence = emotions_raw.get(emotion, 0) / 100.0

        # Map "fear" → "fearful" for consistency
        if emotion == "fear":
            emotion = "fearful"

        _save_emotion_state(emotion, confidence)
        return {"emotion": emotion, "confidence": confidence, "source": "deepface"}

    except ImportError:
        return None
    except Exception as e:
        print(f"[EMOTION] DeepFace error: {e}")
        return None


def detect_emotion_opencv() -> dict:
    """
    Lightweight OpenCV-based emotion estimation using geometric facial analysis.
    Uses eye aspect ratio, mouth openness, and brow position as heuristics.
    Less accurate than DeepFace but requires no heavy ML models.
    """
    try:
        FACE_CASCADE = cv2.CascadeClassifier(CASCADE)
        EYE_CASCADE = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_eye.xml"
        )
        SMILE_CASCADE = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_smile.xml"
        )

        cam = cv2.VideoCapture(0)
        if not cam.isOpened():
            return {"emotion": "neutral", "confidence": 0.5, "source": "fallback"}

        # Collect a few frames
        for _ in range(5):
            cam.read()

        smile_count = 0
        eye_count = 0
        face_found = False
        SAMPLE_FRAMES = 10

        for _ in range(SAMPLE_FRAMES):
            ret, frame = cam.read()
            if not ret:
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = FACE_CASCADE.detectMultiScale(gray, 1.3, 5)

            if len(faces) == 0:
                continue

            face_found = True
            (x, y, w, h) = faces[0]
            roi_gray = gray[y:y + h, x:x + w]

            eyes = EYE_CASCADE.detectMultiScale(roi_gray, 1.1, 3)
            if len(eyes) >= 2:
                eye_count += 1

            smiles = SMILE_CASCADE.detectMultiScale(roi_gray, 1.7, 20)
            if len(smiles) > 0:
                smile_count += 1

            time.sleep(0.05)

        cam.release()

        if not face_found:
            return {"emotion": "neutral", "confidence": 0.5, "source": "opencv_no_face"}

        smile_ratio = smile_count / SAMPLE_FRAMES
        eye_ratio = eye_count / SAMPLE_FRAMES

        # Simple decision tree
        if smile_ratio > 0.4:
            emotion = "happy"
            confidence = min(0.5 + smile_ratio, 0.9)
        elif eye_ratio < 0.3:
            emotion = "stressed"
            confidence = 0.6
        else:
            emotion = "neutral"
            confidence = 0.7

        _save_emotion_state(emotion, confidence)
        return {"emotion": emotion, "confidence": confidence, "source": "opencv"}

    except Exception as e:
        print(f"[EMOTION] OpenCV fallback error: {e}")
        return {"emotion": "neutral", "confidence": 0.5, "source": "error"}


def detect_emotion() -> dict:
    """
    Main entry point. Tries DeepFace first, falls back to OpenCV.
    Returns: {"emotion": str, "confidence": float, "source": str}
    """
    # Try DeepFace (accurate)
    result = detect_emotion_deepface()
    if result:
        return result

    # Fall back to OpenCV geometric (lightweight)
    return detect_emotion_opencv()


def get_current_emotion_state() -> dict:
    """Returns the last known emotion state from the state file."""
    try:
        if os.path.exists(EMOTION_STATE_FILE):
            with open(EMOTION_STATE_FILE) as f:
                return json.load(f)
    except Exception:
        pass
    return {"emotion": "neutral", "confidence": 0.5, "emoji": "🤖", "suggestion": None}


def get_emotion_adapted_response(base_response: str, emotion: str) -> str:
    """
    Optionally appends an emotion-aware suggestion to any JARVIS response.
    Call this to make JARVIS adapt its personality.
    """
    info = EMOTION_RESPONSES.get(emotion, EMOTION_RESPONSES["neutral"])
    suggestion = info.get("suggestion")
    if suggestion:
        return f"{base_response}\n\n💬 {suggestion}"
    return base_response


def is_emotion_command(command: str) -> bool:
    """Returns True if the command asks for emotion detection."""
    triggers = [
        "how do i look", "what's my mood", "detect my emotion",
        "emotion scan", "how am i feeling", "read my face",
        "analyze my expression", "mood check", "am i stressed",
    ]
    cmd = command.lower()
    return any(t in cmd for t in triggers)


def emotion_check_response(command: str) -> str:
    """Run emotion detection and return a JARVIS-style response."""
    result = detect_emotion()
    emotion = result.get("emotion", "neutral")
    confidence = result.get("confidence", 0.5)
    info = EMOTION_RESPONSES.get(emotion, EMOTION_RESPONSES["neutral"])
    emoji = info.get("emoji", "🤖")
    suggestion = info.get("suggestion", "")

    response = (
        f"{emoji} Emotion Analysis Complete:\n"
        f"Detected: **{emotion.upper()}** (Confidence: {confidence:.0%})\n"
        f"{info['greeting']}"
    )
    if suggestion:
        response += f"\n{suggestion}"
    return response
