import cv2
import numpy as np
import time

CASCADE = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"

SCAN_DURATION = 15   # seconds to scan
FPS_TARGET    = 30   # target capture FPS


def _classify_bpm(bpm: float) -> str:
    if bpm < 50:
        return "very low — please rest and check again"
    elif bpm < 60:
        return "low — athlete range or resting state"
    elif bpm < 100:
        return "normal range"
    elif bpm < 120:
        return "slightly elevated — you may be active or stressed"
    else:
        return "high — please rest and consult a doctor if it persists"


def measure_heart_rate() -> str:
    """
    Uses rPPG (remote photoplethysmography) via webcam.
    Detects tiny green channel variations in face caused by blood flow.
    Returns spoken result string.
    """
    detector = cv2.CascadeClassifier(CASCADE)
    cam      = cv2.VideoCapture(0)
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cam.set(cv2.CAP_PROP_FPS, FPS_TARGET)

    green_values = []
    timestamps   = []
    start_time   = time.time()
    face_found   = False

    print("[HEARTBEAT] Starting scan... look at the camera and stay still.")

    while time.time() - start_time < SCAN_DURATION:
        ret, frame = cam.read()
        if not ret:
            continue

        elapsed   = time.time() - start_time
        remaining = int(SCAN_DURATION - elapsed)
        gray      = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # Improve contrast for low-light scenes
        try:
            gray_eq = cv2.equalizeHist(gray)
        except Exception:
            gray_eq = gray

        # Primary detection (moderate strictness)
        faces = detector.detectMultiScale(gray_eq, scaleFactor=1.1, minNeighbors=4, minSize=(60, 60))

        # Fallback: be more lenient if nothing found (handles distance/low-res webcams)
        if len(faces) == 0:
            faces = detector.detectMultiScale(gray_eq, scaleFactor=1.05, minNeighbors=3, minSize=(40, 40))

        if len(faces) > 0:
            face_found = True
            x, y, w, h = faces[0]

            # Use forehead region — most stable for rPPG
            forehead_y1 = y + int(h * 0.08)
            forehead_y2 = y + int(h * 0.35)
            forehead_x1 = x + int(w * 0.15)
            forehead_x2 = x + int(w * 0.85)

            # Clamp coordinates to frame bounds
            h_img, w_img = frame.shape[:2]
            forehead_y1 = max(0, min(forehead_y1, h_img - 1))
            forehead_y2 = max(0, min(forehead_y2, h_img))
            forehead_x1 = max(0, min(forehead_x1, w_img - 1))
            forehead_x2 = max(0, min(forehead_x2, w_img))

            forehead = frame[forehead_y1:forehead_y2, forehead_x1:forehead_x2]

            if forehead.size > 0:
                # Green channel is most sensitive to blood volume changes
                green_mean = np.mean(forehead[:, :, 1])
                green_values.append(green_mean)
                timestamps.append(elapsed)

            # Draw UI
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 180), 2)
            cv2.rectangle(frame, (forehead_x1, forehead_y1),
                          (forehead_x2, forehead_y2), (0, 200, 255), 1)
            cv2.putText(frame, f"Scanning: {len(green_values)} samples",
                        (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 180), 2)
        else:
            cv2.putText(frame, "No face detected — look at camera",
                        (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        cv2.putText(frame, f"JARVIS Heart Rate Monitor | {remaining}s",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 200, 255), 2)

        # Progress bar
        progress = int((elapsed / SCAN_DURATION) * 600)
        cv2.rectangle(frame, (10, 460), (10 + progress, 475), (0, 255, 180), -1)
        cv2.rectangle(frame, (10, 460), (610, 475), (0, 255, 180), 1)

        cv2.imshow("JARVIS - Heart Rate Monitor", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cam.release()
    cv2.destroyAllWindows()

    if not face_found or len(green_values) < 30:
        return "Raj, I couldn't detect your face clearly. Please ensure good lighting and try again."

    # --- Signal processing ---
    green_arr = np.array(green_values)
    time_arr  = np.array(timestamps)

    # Normalize signal
    green_arr = green_arr - np.mean(green_arr)

    # Calculate actual FPS from timestamps
    actual_fps = len(time_arr) / (time_arr[-1] - time_arr[0]) if len(time_arr) > 1 else 25

    # Apply bandpass filter for heart rate range (0.7–3.5 Hz = 42–210 BPM)
    try:
        from scipy.signal import butter, filtfilt

        def bandpass_filter(data, lowcut, highcut, fs, order=4):
            nyq    = 0.5 * fs
            low    = lowcut / nyq
            high   = highcut / nyq
            low    = max(0.01, min(low, 0.99))
            high   = max(0.01, min(high, 0.99))
            if low >= high:
                return data
            b, a = butter(order, [low, high], btype='band')
            return filtfilt(b, a, data)

        filtered = bandpass_filter(green_arr, 0.7, 3.5, actual_fps)

        # FFT to find dominant frequency
        fft_vals  = np.abs(np.fft.rfft(filtered))
        fft_freqs = np.fft.rfftfreq(len(filtered), d=1.0/actual_fps)

        # Only look at heart rate range
        valid_mask = (fft_freqs >= 0.7) & (fft_freqs <= 3.5)
        if not np.any(valid_mask):
            raise ValueError("No valid frequencies")

        peak_freq = fft_freqs[valid_mask][np.argmax(fft_vals[valid_mask])]
        bpm       = peak_freq * 60.0

    except Exception:
        # Simple fallback — count zero crossings
        crossings = np.where(np.diff(np.sign(green_arr)))[0]
        if len(crossings) < 2:
            return "Raj, I couldn't get a clear reading. Please try again in better lighting."
        duration = time_arr[-1] - time_arr[0]
        bpm      = (len(crossings) / 2) / duration * 60

    bpm = round(float(bpm))

    # Sanity check
    if bpm < 40 or bpm > 200:
        return "Raj, the reading was unclear. Please sit still in good lighting and try again."

    status = _classify_bpm(bpm)
    print(f"[HEARTBEAT] Estimated BPM: {bpm}")
    return f"Raj, your estimated heart rate is {bpm} BPM — {status}."
