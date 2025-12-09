import sys
import os
import subprocess
import time
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout, 
                             QWidget, QStackedWidget, QHBoxLayout)
from PyQt6.QtMultimedia import (QMediaCaptureSession, QCamera, QMediaRecorder, 
                                QMediaPlayer, QAudioOutput)
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtCore import QUrl, QTimer, Qt, QSize

# --- KONFIGURACJA ---
RECORDINGS_DIR = os.path.join(os.getcwd(), "recordings")
MAX_RECORDING_TIME_SEC = 600  # 10 minut
WARNING_TIME_SEC = 10         # Czas na reakcję "A"
SECRET_EXIT_KEY = Qt.Key.Key_Q
SECRET_MODIFIER = Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier

class VideoBooth(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Budka Nagrań")
        
        # Tworzenie katalogu na nagrania
        if not os.path.exists(RECORDINGS_DIR):
            os.makedirs(RECORDINGS_DIR)

        self.temp_file = os.path.join(RECORDINGS_DIR, "temp_rec") 

        # --- UI SETUP ---
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Stos widoków (Kamera vs Odtwarzacz)
        self.stack = QStackedWidget()
        self.layout.addWidget(self.stack)

        # 1. Widok Kamery
        self.camera_widget = QVideoWidget()
        self.stack.addWidget(self.camera_widget)

        # 2. Widok Odtwarzacza (Review)
        self.player_widget = QVideoWidget()
        self.stack.addWidget(self.player_widget)
        
        # 3. Overlay informacyjny (Napisy na dole)
        self.info_label = QLabel("Naciśnij SPACJĘ aby rozpocząć")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setStyleSheet("font-size: 36px; color: white; background-color: rgba(0,0,0,150); padding: 20px;")
        self.layout.addWidget(self.info_label)

        # --- MULTIMEDIA SETUP ---
        # Kamera
        self.session = QMediaCaptureSession()
        self.camera = QCamera()
        self.session.setCamera(self.camera)
        self.session.setVideoOutput(self.camera_widget)
        
        # Nagrywanie
        self.recorder = QMediaRecorder()
        self.session.setRecorder(self.recorder)
        
        # Odtwarzanie
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.player.setVideoOutput(self.player_widget)

        # --- LOGIKA STANÓW ---
        # Stany: 'HOME', 'RECORDING', 'REVIEW', 'TIMEOUT_WARNING'
        self.state = 'HOME'
        
        # Timery
        self.rec_timer = QTimer()
        self.rec_timer.timeout.connect(self.update_recording_timer)
        self.rec_seconds = 0

        self.warning_timer = QTimer()
        self.warning_timer.timeout.connect(self.update_warning_timer)
        self.warning_seconds = WARNING_TIME_SEC

        # Start kamery
        self.camera.start()
        
        # Ustawienie Fullscreen
        self.showFullScreen()
        
    def keyPressEvent(self, event):
        # Tajne wyjście: Ctrl + Shift + Q
        if event.modifiers() == SECRET_MODIFIER and event.key() == SECRET_EXIT_KEY:
            self.close()
            return

        if self.state == 'HOME':
            if event.key() == Qt.Key.Key_Space:
                self.start_recording()

        elif self.state == 'RECORDING':
            if event.key() == Qt.Key.Key_Space:
                self.stop_recording()

        elif self.state == 'REVIEW':
            if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
                self.accept_recording()
            elif event.key() == Qt.Key.Key_Escape:
                self.reset_to_home()

        elif self.state == 'TIMEOUT_WARNING':
            if event.key() == Qt.Key.Key_A:
                self.stop_warning_logic()
                self.go_to_review()

    def start_recording(self):
        self.state = 'RECORDING'
        # Ważne: Wymuszamy rozszerzenie .webm dla stabilności
        self.recorder.setOutputLocation(QUrl.fromLocalFile(self.temp_file + ".webm"))
        self.recorder.record()
        
        self.rec_seconds = 0
        self.rec_timer.start(1000)
        
        # --- POPRAWKA: Bezpośrednie ustawienie tekstu zamiast błędnej funkcji ---
        self.info_label.setText(f"NAGRYWANIE: 00:00 (SPACJA aby zatrzymać)")
        self.info_label.setStyleSheet("font-size: 36px; color: red; background-color: rgba(0,0,0,150); padding: 20px;")

    def stop_recording(self):
        self.recorder.stop()
        self.rec_timer.stop()
        # Czekamy chwilę na zamknięcie pliku przez system
        QTimer.singleShot(500, self.go_to_review)

    def update_recording_timer(self):
        self.rec_seconds += 1
        time_str = self.format_time(self.rec_seconds)
        self.info_label.setText(f"NAGRYWANIE: {time_str} (SPACJA aby zatrzymać)")
        
        # Sprawdzenie limitu czasu
        if self.rec_seconds >= MAX_RECORDING_TIME_SEC:
            self.trigger_timeout_warning()

    def trigger_timeout_warning(self):
        self.state = 'TIMEOUT_WARNING'
        self.recorder.stop() 
        self.rec_timer.stop()
        self.warning_seconds = WARNING_TIME_SEC
        self.warning_timer.start(1000)
        self.update_warning_label()

    def update_warning_timer(self):
        self.warning_seconds -= 1
        self.update_warning_label()
        
        if self.warning_seconds <= 0:
            self.warning_timer.stop()
            self.reset_to_home() 

    def update_warning_label(self):
        self.info_label.setText(f"Koniec czasu! Reset za {self.warning_seconds}s. Naciśnij 'A' aby zachować.")
        self.info_label.setStyleSheet("font-size: 36px; color: red; background-color: black; padding: 20px;")

    def stop_warning_logic(self):
        self.warning_timer.stop()
        self.info_label.setStyleSheet("font-size: 36px; color: white; background-color: rgba(0,0,0,150); padding: 20px;")

    def go_to_review(self):
        self.state = 'REVIEW'
        self.stack.setCurrentWidget(self.player_widget)
        self.camera.stop()
        
        real_file = self.find_actual_recording_file()
        if real_file:
            self.player.setSource(QUrl.fromLocalFile(real_file))
            self.player.play()
            self.player.mediaStatusChanged.connect(self.loop_video)
        
        self.info_label.setText("Podgląd. ENTER: Akceptuj | ESC: Odrzuć")
        self.info_label.setStyleSheet("font-size: 36px; color: white; background-color: rgba(0,0,0,150); padding: 20px;")

    def find_actual_recording_file(self):
        for f in os.listdir(RECORDINGS_DIR):
            if f.startswith("temp_rec"):
                return os.path.join(RECORDINGS_DIR, f)
        return None

    def loop_video(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.player.play()

    def accept_recording(self):
        self.player.stop()
        real_file = self.find_actual_recording_file()
        
        if real_file:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            output_file = os.path.join(RECORDINGS_DIR, f"video_{timestamp}.mp4")
            
            self.info_label.setText("Zapisywanie... Proszę czekać.")
            QApplication.processEvents() 
            
            cmd = [
                "ffmpeg", "-i", real_file,
                "-c:v", "libx264", "-preset", "fast",
                "-c:a", "aac",
                output_file, "-y"
            ]
            
            try:
                subprocess.run(cmd, check=True)
                print(f"Zapisano: {output_file}")
            except subprocess.CalledProcessError as e:
                print(f"Błąd konwersji: {e}")

        self.reset_to_home()

    def reset_to_home(self):
        self.player.stop()
        self.player.setSource(QUrl())
        self.state = 'HOME'
        
        for f in os.listdir(RECORDINGS_DIR):
            if f.startswith("temp_rec"):
                try:
                    os.remove(os.path.join(RECORDINGS_DIR, f))
                except OSError:
                    pass

        self.stack.setCurrentWidget(self.camera_widget)
        self.camera.start()
        self.info_label.setText("Naciśnij SPACJĘ aby rozpocząć")
        self.info_label.setStyleSheet("font-size: 36px; color: white; background-color: rgba(0,0,0,150); padding: 20px;")

    def format_time(self, seconds):
        m, s = divmod(seconds, 60)
        return f"{m:02d}:{s:02d}"

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoBooth()
    window.show()
    sys.exit(app.exec())
