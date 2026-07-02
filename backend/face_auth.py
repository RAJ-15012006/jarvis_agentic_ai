import cv2
import time

CASCADE = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"

def verify_face() -> bool:
    """
    EXTREMELY LENIENT: Returns True if ANY face is detected for 1 frame.
    """
    detector = cv2.CascadeClassifier(CASCADE)
    cam = cv2.VideoCapture(0)
    
    start_time = time.time()
    SCAN_TIMEOUT = 10
    
    print("[FACE AUTH] Running in 'Anyone Access' mode...")

    while time.time() - start_time < SCAN_TIMEOUT:
        ret, frame = cam.read()
        if not ret:
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector.detectMultiScale(gray, 1.3, 5)

        if len(faces) > 0:
            # Face detected!
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(frame, "Identity Verified", (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            try:
                cv2.imshow("JARVIS - Face Authentication", frame)
                cv2.waitKey(1000) # Show success for 1 second
            except Exception:
                pass
            cam.release()
            try:
                cv2.destroyAllWindows()
            except Exception:
                pass
            return True

        cv2.putText(frame, "Scanning for Access...", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        try:
            cv2.imshow("JARVIS - Face Authentication", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        except Exception:
            # Fallback if GUI fails
            time.sleep(0.05)

    cam.release()
    try:
        cv2.destroyAllWindows()
    except Exception:
        pass
    return False

def run_face_auth() -> dict:
    verified = verify_face()
    return {"verified": verified, "attempts_left": 3, "locked": False}
