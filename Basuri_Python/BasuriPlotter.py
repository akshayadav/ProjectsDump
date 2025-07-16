import numpy as np
import sounddevice as sd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy.fft import fft
from datetime import datetime
from collections import deque

# Parameters
duration = 0.10  # seconds per analysis
fs = 44100       # sampling rate
window_size = 60  # seconds of data to show

# Data storage
timestamps = deque(maxlen=int(window_size / duration))
frequencies = deque(maxlen=int(window_size / duration))
amplitudes = deque(maxlen=int(window_size / duration))  # Store amplitude

def detect_frequency(audio, fs):
    N = len(audio)
    yf = np.abs(fft(audio))
    xf = np.fft.fftfreq(N, 1 / fs)
    idx = np.argmax(yf[:N // 2])
    freq = abs(xf[idx])
    amp = np.max(yf[:N // 2])  # Amplitude at dominant frequency
    return freq, amp

def audio_callback(indata, frames, time, status):
    audio = indata[:, 0]
    freq, amp = detect_frequency(audio, fs)
    now = datetime.now()
    timestamps.append(now)
    frequencies.append(freq)
    amplitudes.append(amp)

# Set up matplotlib
plt.ion()
fig, ax1 = plt.subplots()
ax2 = ax1.twinx()  # Second y-axis for amplitude

line1, = ax1.plot([], [], label="Detected Frequency", color='b')
line2, = ax2.plot([], [], label="Amplitude", color='orange')
ax1.axhline(440, color='r', linestyle='--', label='A4 (440 Hz)')
ax1.set_xlabel("Time")
ax1.set_ylabel("Frequency (Hz)", color='b')
ax2.set_ylabel("Amplitude", color='orange')
ax1.set_ylim(0, 1000)
ax2.set_ylim(0, 1e7)  # You may need to adjust this based on your input
ax1.legend(loc='upper left')
ax2.legend(loc='upper right')

def update_plot():
    if len(timestamps) > 0:
        ax1.clear()
        ax2.clear()
        ax1.plot(timestamps, frequencies, label="Detected Frequency", color='b')
        ax2.plot(timestamps, amplitudes, label="Amplitude", color='orange')
        ax1.axhline(440, color='r', linestyle='--', label='A4 (440 Hz)')
        ax1.set_xlabel("Time")
        ax1.set_ylabel("Frequency (Hz)", color='b')
        ax2.set_ylabel("Amplitude", color='orange')
        # Find current min and max frequency in the window
        min_freq = min(frequencies)
        max_freq = max(frequencies)
        delta = max(abs(max_freq - 440), abs(min_freq - 440), 100)
        ax1.set_ylim(440 - delta, 440 + delta)
        # Amplitude axis autoscale
        ax2.set_ylim(0, max(max(amplitudes), 1e5))
        ax1.legend(loc='upper left')
        ax2.legend(loc='upper right')
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        fig.autofmt_xdate()

        # Annotate peaks, valleys, and significant amplitude jumps
        y = np.array(frequencies)
        x = np.array(timestamps)
        a = np.array(amplitudes)
        if len(y) > 2:
            amp_threshold = 1e5  # Adjust as needed for "big amplitude difference"
            for i in range(1, len(y) - 1):
                # Peak
                if y[i] > y[i-1] and y[i] > y[i+1]:
                    ax1.annotate(f"{y[i]:.1f} Hz\n{a[i]:.0f}", (x[i], y[i]), textcoords="offset points", xytext=(0,10), ha='center', color='blue', fontsize=8)
                # Valley
                elif y[i] < y[i-1] and y[i] < y[i+1]:
                    ax1.annotate(f"{y[i]:.1f} Hz\n{a[i]:.0f}", (x[i], y[i]), textcoords="offset points", xytext=(0,-15), ha='center', color='green', fontsize=8)
                # Significant jump in amplitude from previous value
                elif abs(a[i] - a[i-1]) > amp_threshold:
                    ax1.annotate(f"{y[i]:.1f} Hz\n{a[i]:.0f}", (x[i], y[i]), textcoords="offset points", xytext=(0,5), ha='center', color='purple', fontsize=8)

        plt.pause(0.01)

print("Listening... Speak or play a note.")

with sd.InputStream(callback=audio_callback, channels=1, samplerate=fs, blocksize=int(fs * duration)):
    while True:
        sd.sleep(int(duration * 1000))
        update_plot()