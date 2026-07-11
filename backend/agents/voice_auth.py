import os
import io
import numpy as np
import scipy.io.wavfile as wav
from scipy.fftpack import dct

# Directory to store biometric profiles
BIOMETRIC_DIR = os.path.join(os.path.dirname(__file__), "face_data")
VOICE_PROFILE_PATH = os.path.join(BIOMETRIC_DIR, "voice_profile.npy")
os.makedirs(BIOMETRIC_DIR, exist_ok=True)

# Cosine similarity matching threshold
# Values above this indicate the voice matches Raj's profile.
SIMILARITY_THRESHOLD = 0.82


def extract_mfcc_profile(audio_bytes: bytes) -> np.ndarray:
    """
    Decodes WAV bytes and extracts a 26-dimensional voice profile vector:
      - 13 Mel-Frequency Cepstral Coefficients (MFCC) averages
      - 13 MFCC standard deviations
    Returns None if audio decoding fails.
    """
    try:
        # Load WAV bytes
        sample_rate, audio_data = wav.read(io.BytesIO(audio_bytes))

        # Handle stereo -> mono conversion
        if len(audio_data.shape) > 1:
            audio_data = audio_data.mean(axis=1)

        # Normalize audio signal
        audio_data = audio_data.astype(np.float32)
        if np.max(np.abs(audio_data)) > 0:
            audio_data /= np.max(np.abs(audio_data))

        # Pre-emphasis filter
        pre_emphasis = 0.97
        emphasized_signal = np.append(audio_data[0], audio_data[1:] - pre_emphasis * audio_data[:-1])

        # Framing config
        frame_size = 0.025  # 25 ms
        frame_stride = 0.01  # 10 ms
        frame_length, frame_step = frame_size * sample_rate, frame_stride * sample_rate
        signal_length = len(emphasized_signal)
        frame_length = int(round(frame_length))
        frame_step = int(round(frame_step))

        # Stop if audio clip is too short
        if signal_length < frame_length:
            return None

        num_frames = int(np.ceil(float(np.abs(signal_length - frame_length)) / frame_step))
        pad_signal_length = num_frames * frame_step + frame_length
        z = np.zeros((pad_signal_length - signal_length))
        pad_signal = np.append(emphasized_signal, z)

        indices = np.tile(np.arange(0, frame_length), (num_frames, 1)) + \
                  np.tile(np.arange(0, num_frames * frame_step, frame_step), (frame_length, 1)).T
        frames = pad_signal[indices.astype(np.int32, copy=False)]

        # Windowing (Hamming)
        frames *= np.hamming(frame_length)

        # Fourier Transform & Power Spectrum
        NFFT = 512
        mag_frames = np.absolute(np.fft.rfft(frames, NFFT))
        pow_frames = ((1.0 / NFFT) * ((mag_frames) ** 2))

        # Mel Filterbanks
        low_freq_mel = 0
        high_freq_mel = (2595 * np.log10(1 + (sample_rate / 2) / 700))
        mel_points = np.linspace(low_freq_mel, high_freq_mel, 40)
        hz_points = (700 * (10**(mel_points / 2595) - 1))
        bin = np.floor((NFFT + 1) * hz_points / sample_rate)

        fbank = np.zeros((38, int(np.floor(NFFT / 2 + 1))))
        for m in range(1, 39):
            f_m_minus = int(bin[m - 1])
            f_m = int(bin[m])
            f_m_plus = int(bin[m + 1])
            for k in range(f_m_minus, f_m):
                fbank[m - 1, k] = (k - bin[m - 1]) / (bin[m] - bin[m - 1])
            for k in range(f_m, f_m_plus):
                fbank[m - 1, k] = (bin[m + 1] - k) / (bin[m + 1] - bin[m])

        filter_banks = np.dot(pow_frames, fbank.T)
        filter_banks = np.where(filter_banks == 0, np.finfo(float).eps, filter_banks)
        filter_banks = 20 * np.log10(filter_banks)

        # Discrete Cosine Transform (DCT)
        num_ceps = 13
        mfcc = dct(filter_banks, type=2, axis=1, norm='ortho')[:, 1:(num_ceps + 1)]

        # Mean Normalization
        mfcc -= (np.mean(mfcc, axis=0) + 1e-8)

        # Calculate average and standard deviation to build voice signature
        mean_profile = np.mean(mfcc, axis=0)
        std_profile = np.std(mfcc, axis=0)

        # Concat to get 26-dim vector
        voice_vector = np.concatenate([mean_profile, std_profile])
        return voice_vector
    except Exception as e:
        print(f"[VOICE AUTH ERROR]: {e}")
        return None


def register_voice_profile(samples: list[bytes]) -> bool:
    """
    Takes 3 WAV voice samples, extracts profiles, averages them, and saves.
    """
    extracted_profiles = []
    for sample in samples:
        profile = extract_mfcc_profile(sample)
        if profile is not None:
            extracted_profiles.append(profile)

    if len(extracted_profiles) < 2:
        print("[VOICE AUTH] Failed: Not enough valid voice samples parsed.")
        return False

    # Average the profiles
    avg_profile = np.mean(extracted_profiles, axis=0)
    np.save(VOICE_PROFILE_PATH, avg_profile)
    print(f"[VOICE AUTH] Raj's voice profile registered at {VOICE_PROFILE_PATH}")
    return True


def verify_speaker(audio_bytes: bytes) -> tuple[bool, float]:
    """
    Compares the voice sample against Raj's registered voice profile.
    Returns (is_matched, similarity_score).
    """
    if not os.path.exists(VOICE_PROFILE_PATH):
        # Auto-approve if voice profile is not registered yet (e.g. fresh installation)
        print("[VOICE AUTH] Profile not registered. Auto-approving speaker.")
        return True, 1.0

    current_profile = extract_mfcc_profile(audio_bytes)
    if current_profile is None:
        print("[VOICE AUTH] Failed to extract voice signature.")
        return False, 0.0

    ref_profile = np.load(VOICE_PROFILE_PATH)

    # Compute Cosine Similarity
    dot_prod = np.dot(current_profile, ref_profile)
    norm_a = np.linalg.norm(current_profile)
    norm_b = np.linalg.norm(ref_profile)

    if norm_a == 0 or norm_b == 0:
        return False, 0.0

    similarity = dot_prod / (norm_a * norm_b)
    is_raj = bool(similarity >= SIMILARITY_THRESHOLD)
    score = float(similarity)

    print(f"[VOICE AUTH] Speaker similarity score: {score:.4f} (Match: {is_raj})")
    return is_raj, score
