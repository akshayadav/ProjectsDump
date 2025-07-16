import numpy as np
import sounddevice as sd
from scipy.fft import fft

# Note frequencies for the Western chromatic scale (A4 = 440 Hz)
NOTE_FREQS = {
    'C4': 261.63, 'C#4': 277.18, 'D4': 293.66, 'D#4': 311.13, 'E4': 329.63,
    'F4': 349.23, 'F#4': 369.99, 'G4': 392.00, 'G#4': 415.30, 'A4': 440.00,
    'A#4': 466.16, 'B4': 493.88, 'C5': 523.25
}

def freq_to_note(freq):
    min_diff = float('inf')
    note = None
    for n, f in NOTE_FREQS.items():
        diff = abs(freq - f)
        if diff < min_diff:
            min_diff = diff
            note = n
    return note

def detect_note(audio, fs):
    # FFT
    N = len(audio)
    yf = np.abs(fft(audio))
    xf = np.fft.fftfreq(N, 1 / fs)
    # Only look at positive frequencies
    idx = np.argmax(yf[:N // 2])
    freq = abs(xf[idx])
    note = freq_to_note(freq)
    return note, freq

def callback(indata, frames, time, status):
    audio = indata[:, 0]
    note, freq = detect_note(audio, fs)
    print(f"Detected Note: {note} (Frequency: {freq:.2f} Hz)")

# Parameters
# duration = 2  # seconds per analysis
duration = 0.25  # seconds per analysis
fs = 44100    # sampling rate

print("Listening... Play a note on your Basuri.")

with sd.InputStream(callback=callback, channels=1, samplerate=fs, blocksize=int(fs * duration)):
    while True:
        sd.sleep(int(duration * 1000))




