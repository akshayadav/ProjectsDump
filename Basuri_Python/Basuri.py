import sys
import sounddevice as sd
import numpy as np
import threading
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QPainter, QColor
from PyQt5.QtCore import Qt, QTimer

NOTES_FREQ = {
    'C4': 261.63, 'C#4': 277.18, 'D4': 293.66, 'D#4': 311.13, 'E4': 329.63,
    'F4': 349.23, 'F#4': 369.99, 'G4': 392.00, 'G#4': 415.30, 'A4': 440.00,
    'A#4': 466.16, 'B4': 493.88, 'C5': 523.25
}
NOTE_ORDER = ['C4', 'C#4', 'D4', 'D#4', 'E4', 'F4', 'F#4', 'G4', 'G#4', 'A4', 'A#4', 'B4', 'C5']

def freq_to_note(freq):
    print(f"Detected frequency: {freq:.2f} Hz")
    min_diff = float('inf')
    closest_note = None
    for note, note_freq in NOTES_FREQ.items():
        diff = abs(freq - note_freq)
        if diff < min_diff:
            min_diff = diff
            closest_note = note
    return closest_note

class BasuriGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Basuri Note Recognizer")
        self.setGeometry(100, 100, 200, 500)
        self.active_note = None
        self.listening = True
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(100)
        threading.Thread(target=self.listen_mic, daemon=True).start()

    def paintEvent(self, event):
        qp = QPainter(self)
        spacing = 70
        radius = 30
        for i, note in enumerate(NOTE_ORDER):
            x = 100
            y = 50 + i * spacing
            color = QColor('green') if note == self.active_note else QColor('gray')
            qp.setBrush(color)
            qp.setPen(Qt.black)
            qp.drawEllipse(x - radius, y - radius, radius * 2, radius * 2)
            qp.setPen(Qt.black)
            qp.drawText(x - 10, y + 5, note)

    def listen_mic(self):
        def callback(indata, frames, time, status):
            if not self.listening:
                return
            audio = indata[:, 0]
            fft = np.fft.rfft(audio)
            freqs = np.fft.rfftfreq(len(audio), 1/44100)
            idx = np.argmax(np.abs(fft))
            freq = freqs[idx]
            note = freq_to_note(freq)
            if note and note != self.active_note:
                self.active_note = note
        with sd.InputStream(channels=1, callback=callback, samplerate=44100, blocksize=2048):
            while self.listening:
                sd.sleep(100)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = BasuriGUI()
    gui.show()
    sys.exit(app.exec_())