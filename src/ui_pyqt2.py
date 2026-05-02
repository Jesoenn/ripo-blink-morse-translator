import sys
import cv2
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QLabel, QWidget, 
                             QVBoxLayout, QHBoxLayout, QSlider, QFormLayout, QGroupBox, QProgressBar, QSizePolicy, QFrame, QCheckBox, QScrollArea)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QImage, QPixmap

from image_utils import enhance_frame
from detector import EyeDetector
from engine import MorseEngine
import config
from qt_material import apply_stylesheet

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Blink To Morse Translator")
        self.setMinimumSize(1000, 700)
        
        # Init camera and models
        self.cap = cv2.VideoCapture(0)
        self.detector = EyeDetector()
        self.engine = MorseEngine()
        
        # Central Widget & Root Layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.root_layout = QVBoxLayout(self.central_widget)
        self.root_layout.setContentsMargins(20, 20, 20, 20)
        self.root_layout.setSpacing(15)
        
        # --- TOP: App Title ---
        self.title_label = QLabel("BLINK TO MORSE TRANSLATOR")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-size: 28px; font-weight: 900; color: #4db6ac; letter-spacing: 2px;")
        self.root_layout.addWidget(self.title_label)
        
        # --- MIDDLE: Content Layout (Left + Right panels) ---
        self.content_layout = QHBoxLayout()
        self.root_layout.addLayout(self.content_layout)
        
        # ================= LEFT PANEL =================
        self.left_panel = QWidget()
        self.left_layout = QVBoxLayout(self.left_panel)
        self.left_layout.setContentsMargins(0, 0, 0, 0)
        self.left_layout.setSpacing(15)
        
        # 1. Camera Box (Resizes, expanding)
        self.video_container = QFrame()
        self.video_container.setStyleSheet("background-color: #121212; border-radius: 12px; border: 2px solid #26a69a;")
        self.video_layout = QVBoxLayout(self.video_container)
        self.video_layout.setContentsMargins(2, 2, 2, 2)
        
        self.video_label = QLabel("Włączanie kamery...")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.video_label.setMinimumSize(640, 360)
        self.video_layout.addWidget(self.video_label)
        
        self.left_layout.addWidget(self.video_container, stretch=1)
        
        # 2. Translated Text Box (Below Camera)
        self.morse_group = QGroupBox("Tłumaczenie Tekstu")
        self.morse_group.setStyleSheet("QGroupBox { font-size: 16px; font-weight: bold; }")
        self.morse_layout = QVBoxLayout()
        self.morse_layout.setSpacing(5)
        
        self.seq_label = QLabel("Sekwencja: ")
        self.seq_label.setStyleSheet("font-size: 20px; color: #80cbc4; font-family: 'Courier New', monospace;")
        self.seq_label.setWordWrap(True)
        self.seq_label.setMinimumHeight(50)
        
        self.text_label = QLabel("Tekst: ")
        self.text_label.setStyleSheet("font-size: 32px; font-weight: bold; color: #ffffff;")
        self.text_label.setWordWrap(True)
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.text_label.setMinimumHeight(80) 
        
        self.morse_layout.addWidget(self.seq_label)
        self.morse_layout.addWidget(self.text_label)
        self.morse_group.setLayout(self.morse_layout)
        self.left_layout.addWidget(self.morse_group)
        
        self.content_layout.addWidget(self.left_panel, stretch=1)
        
        # ================= RIGHT PANEL =================
        self.right_scroll = QScrollArea()
        self.right_scroll.setFixedWidth(380)
        self.right_scroll.setWidgetResizable(True)
        self.right_scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout(self.right_panel)
        self.right_layout.setContentsMargins(15, 0, 15, 0)
        self.right_layout.setSpacing(20)
        
        self.right_scroll.setWidget(self.right_panel)
        
        # 1. Debug Info
        self.info_group = QGroupBox("Status Kamery i Twarzy")
        self.info_group.setStyleSheet("QGroupBox { font-size: 14px; font-weight: bold; }")
        self.info_layout = QVBoxLayout()
        self.info_layout.setSpacing(10)
        
        self.status_label = QLabel("Status: WAIT")
        self.left_ear_label = QLabel("Lewe Oko EAR: 0.00")
        self.right_ear_label = QLabel("Prawe Oko EAR: 0.00")
        self.is_closed_label = QLabel("Mrugnięcie: NIE")
        
        for lbl in (self.status_label, self.left_ear_label, self.right_ear_label, self.is_closed_label):
            lbl.setStyleSheet("font-size: 16px;")
            self.info_layout.addWidget(lbl)
            
        self.info_group.setLayout(self.info_layout)
        self.right_layout.addWidget(self.info_group)
        
        # 2. Timing/Pauses
        self.pause_group = QGroupBox("Detekcja Znaków / Słów (Pauzy)")
        self.pause_group.setStyleSheet("QGroupBox { font-size: 14px; font-weight: bold; }")
        self.pause_layout = QVBoxLayout()
        self.pause_layout.setSpacing(15)
        
        self.char_bar = QProgressBar()
        self.char_bar.setMaximum(100)
        self.char_bar.setFormat("Znak (Char): %p%")
        self.char_bar.setStyleSheet("QProgressBar::chunk { background-color: #29b6f6; }")
        self.pause_layout.addWidget(self.char_bar)
        
        self.word_bar = QProgressBar()
        self.word_bar.setMaximum(100)
        self.word_bar.setFormat("Słowo (Word): %p%")
        self.word_bar.setStyleSheet("QProgressBar::chunk { background-color: #ab47bc; }")
        self.pause_layout.addWidget(self.word_bar)
        
        self.pause_group.setLayout(self.pause_layout)
        self.right_layout.addWidget(self.pause_group)
        
        # 3. Sliders / Settings
        self.sliders_group = QGroupBox("Parametry Algorytmu")
        self.sliders_group.setStyleSheet("QGroupBox { font-size: 14px; font-weight: bold; }")
        self.sliders_layout = QFormLayout()
        self.sliders_layout.setSpacing(12)
        
        self.min_blink_slider = QSlider(Qt.Orientation.Horizontal)
        self.min_blink_slider.setRange(10, 500)
        self.min_blink_slider.setValue(int(config.MIN_BLINK_DURATION * 1000))
        self.min_blink_label = QLabel(f"{config.MIN_BLINK_DURATION * 1000:.0f} ms")
        self.min_blink_slider.valueChanged.connect(self.update_min_blink)
        self.sliders_layout.addRow("Minimalny czas mrug.:", self.min_blink_slider)
        self.sliders_layout.addRow("", self.min_blink_label)
        
        self.max_blink_slider = QSlider(Qt.Orientation.Horizontal)
        self.max_blink_slider.setRange(300, 3000)
        self.max_blink_slider.setValue(int(config.MAX_BLINK_DURATION * 1000))
        self.max_blink_label = QLabel(f"{config.MAX_BLINK_DURATION * 1000:.0f} ms")
        self.max_blink_slider.valueChanged.connect(self.update_max_blink)
        self.sliders_layout.addRow("Maksymalny czas mrug.:", self.max_blink_slider)
        self.sliders_layout.addRow("", self.max_blink_label)
        
        self.tol_slider = QSlider(Qt.Orientation.Horizontal)
        self.tol_slider.setRange(1, 500)
        self.tol_slider.setValue(int(config.FACE_CENTER_TOLERANCE * 1000))
        self.tol_label = QLabel(f"{config.FACE_CENTER_TOLERANCE:.3f}")
        self.tol_slider.valueChanged.connect(self.update_tol)
        self.sliders_layout.addRow("Ruch twarzy (Tolerancja):", self.tol_slider)
        self.sliders_layout.addRow("", self.tol_label)
        
        self.close_th_slider = QSlider(Qt.Orientation.Horizontal)
        self.close_th_slider.setRange(5, 100)
        self.close_th_slider.setValue(int(config.BLINK_CLOSE_THRESHOLD * 100))
        self.close_th_label = QLabel(f"{config.BLINK_CLOSE_THRESHOLD:.2f}")
        self.close_th_slider.valueChanged.connect(self.update_close_th)
        self.sliders_layout.addRow("Zamykanie oka EAR < :", self.close_th_slider)
        self.sliders_layout.addRow("", self.close_th_label)

        self.open_th_slider = QSlider(Qt.Orientation.Horizontal)
        self.open_th_slider.setRange(5, 100)
        self.open_th_slider.setValue(int(config.BLINK_OPEN_THRESHOLD * 100))
        self.open_th_label = QLabel(f"{config.BLINK_OPEN_THRESHOLD:.2f}")
        self.open_th_slider.valueChanged.connect(self.update_open_th)
        self.sliders_layout.addRow("Otwieranie oka EAR > :", self.open_th_slider)
        self.sliders_layout.addRow("", self.open_th_label)

        self.dot_max_slider = QSlider(Qt.Orientation.Horizontal)
        self.dot_max_slider.setRange(100, 2000)
        self.dot_max_slider.setValue(int(config.DOT_MAX_TIME * 1000))
        self.dot_max_label = QLabel(f"{config.DOT_MAX_TIME * 1000:.0f} ms")
        self.dot_max_slider.valueChanged.connect(self.update_dot_max)
        self.sliders_layout.addRow("Max czas kropki:", self.dot_max_slider)
        self.sliders_layout.addRow("", self.dot_max_label)

        self.dash_min_slider = QSlider(Qt.Orientation.Horizontal)
        self.dash_min_slider.setRange(100, 3000)
        self.dash_min_slider.setValue(int(config.DASH_MIN_TIME * 1000))
        self.dash_min_label = QLabel(f"{config.DASH_MIN_TIME * 1000:.0f} ms")
        self.dash_min_slider.valueChanged.connect(self.update_dash_min)
        self.sliders_layout.addRow("Min czas kreski:", self.dash_min_slider)
        self.sliders_layout.addRow("", self.dash_min_label)

        self.char_pause_slider = QSlider(Qt.Orientation.Horizontal)
        self.char_pause_slider.setRange(100, 5000)
        self.char_pause_slider.setValue(int(config.CHAR_PAUSE * 1000))
        self.char_pause_label = QLabel(f"{config.CHAR_PAUSE * 1000:.0f} ms")
        self.char_pause_slider.valueChanged.connect(self.update_char_pause)
        self.sliders_layout.addRow("Pauza znaku:", self.char_pause_slider)
        self.sliders_layout.addRow("", self.char_pause_label)

        self.word_pause_slider = QSlider(Qt.Orientation.Horizontal)
        self.word_pause_slider.setRange(500, 10000)
        self.word_pause_slider.setValue(int(config.WORD_PAUSE * 1000))
        self.word_pause_label = QLabel(f"{config.WORD_PAUSE * 1000:.0f} ms")
        self.word_pause_slider.valueChanged.connect(self.update_word_pause)
        self.sliders_layout.addRow("Pauza słowa/spacja:", self.word_pause_slider)
        self.sliders_layout.addRow("", self.word_pause_label)

        self.text_clear_slider = QSlider(Qt.Orientation.Horizontal)
        self.text_clear_slider.setRange(1000, 20000)
        self.text_clear_slider.setValue(int(config.TEXT_CLEAR * 1000))
        self.text_clear_label = QLabel(f"{config.TEXT_CLEAR * 1000:.0f} ms")
        self.text_clear_slider.valueChanged.connect(self.update_text_clear)
        self.sliders_layout.addRow("Czas czyszczenia tekstu:", self.text_clear_slider)
        self.sliders_layout.addRow("", self.text_clear_label)
        
        self.sliders_group.setLayout(self.sliders_layout)
        self.right_layout.addWidget(self.sliders_group)
        
        # 4. Toggles / Image Options
        self.toggles_group = QGroupBox("Opcje obrazu")
        self.toggles_group.setStyleSheet("QGroupBox { font-size: 14px; font-weight: bold; }")
        self.toggles_layout = QVBoxLayout()
        self.toggles_layout.setSpacing(10)

        self.cb_clahe = QCheckBox("Włącz CLAHE")
        self.cb_clahe.setChecked(config.ENABLE_CLAHE)
        self.cb_clahe.stateChanged.connect(self.toggle_clahe)
        self.toggles_layout.addWidget(self.cb_clahe)

        self.cb_noise = QCheckBox("Redukcja szumów")
        self.cb_noise.setChecked(config.ENABLE_NOISE_REDUCTION)
        self.cb_noise.stateChanged.connect(self.toggle_noise)
        self.toggles_layout.addWidget(self.cb_noise)

        self.cb_brightness = QCheckBox("Normalizacja jasności")
        self.cb_brightness.setChecked(config.ENABLE_BRIGHTNESS_NORMALIZATION)
        self.cb_brightness.stateChanged.connect(self.toggle_brightness)
        self.toggles_layout.addWidget(self.cb_brightness)

        self.cb_facemesh = QCheckBox("Pokaż Facemesh")
        self.cb_facemesh.setChecked(config.SHOW_FACEMESH)
        self.cb_facemesh.stateChanged.connect(self.toggle_facemesh)
        self.toggles_layout.addWidget(self.cb_facemesh)

        self.cb_processed = QCheckBox("Pokaż przetworzoną twarz (jeśli możliwe)")
        self.cb_processed.setChecked(config.SHOW_PROCESSED_FACE)
        self.cb_processed.stateChanged.connect(self.toggle_processed)
        self.toggles_layout.addWidget(self.cb_processed)

        self.toggles_group.setLayout(self.toggles_layout)
        self.right_layout.addWidget(self.toggles_group)

        self.right_layout.addStretch()
        self.content_layout.addWidget(self.right_scroll)
        
        # Engine Update Timer (~30 fps)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)
        
    def update_min_blink(self, value):
        val = max(value / 1000.0, 0.001)
        config.MIN_BLINK_DURATION = val
        self.min_blink_label.setText(f"{value} ms")
        
    def update_max_blink(self, value):
        val = value / 1000.0
        if val < config.MIN_BLINK_DURATION:
            val = config.MIN_BLINK_DURATION
            self.max_blink_slider.setValue(int(val * 1000))
        config.MAX_BLINK_DURATION = val
        self.max_blink_label.setText(f"{int(val * 1000)} ms")
        
    def update_tol(self, value):
        val = max(value / 1000.0, 0.001)
        config.FACE_CENTER_TOLERANCE = val
        self.tol_label.setText(f"{val:.3f}")

    def update_close_th(self, value):
        val = value / 100.0
        config.BLINK_CLOSE_THRESHOLD = val
        self.close_th_label.setText(f"{val:.2f}")

    def update_open_th(self, value):
        val = value / 100.0
        config.BLINK_OPEN_THRESHOLD = val
        self.open_th_label.setText(f"{val:.2f}")

    def update_dot_max(self, value):
        val = value / 1000.0
        config.DOT_MAX_TIME = val
        self.dot_max_label.setText(f"{value} ms")

    def update_dash_min(self, value):
        val = value / 1000.0
        config.DASH_MIN_TIME = val
        self.dash_min_label.setText(f"{value} ms")

    def update_char_pause(self, value):
        val = value / 1000.0
        config.CHAR_PAUSE = val
        self.char_pause_label.setText(f"{value} ms")

    def update_word_pause(self, value):
        val = value / 1000.0
        config.WORD_PAUSE = val
        self.word_pause_label.setText(f"{value} ms")

    def update_text_clear(self, value):
        val = value / 1000.0
        config.TEXT_CLEAR = val
        self.text_clear_label.setText(f"{value} ms")

    def toggle_clahe(self, state):
        config.ENABLE_CLAHE = bool(state)

    def toggle_noise(self, state):
        config.ENABLE_NOISE_REDUCTION = bool(state)

    def toggle_brightness(self, state):
        config.ENABLE_BRIGHTNESS_NORMALIZATION = bool(state)

    def toggle_facemesh(self, state):
        config.SHOW_FACEMESH = bool(state)

    def toggle_processed(self, state):
        config.SHOW_PROCESSED_FACE = bool(state)

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return
            
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        
        processed = enhance_frame(frame)
        results = self.detector.process(processed)
        
        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0].landmark
            left_ear, right_ear = self.detector.calculate_ear_both_eyes(landmarks, w, h)
            face_center, bbox = self.detector.face_center_and_bbox(landmarks, w, h)
            self.engine.update(left_ear, right_ear, face_center=face_center, frame_size=(w, h))

        display_frame = processed if config.SHOW_PROCESSED_FACE else frame
        if config.SHOW_FACEMESH and results.multi_face_landmarks:
            self.detector.draw_facemesh(display_frame, results)

        # Scale QImage keeping aspect ratio for smooth window resizing
        rgb_image = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
        h_img, w_img, ch = rgb_image.shape
        bytes_per_line = ch * w_img
        q_img = QImage(rgb_image.data, w_img, h_img, bytes_per_line, QImage.Format.Format_RGB888)
        
        pixmap = QPixmap.fromImage(q_img)
        scaled_pixmap = pixmap.scaled(self.video_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.video_label.setPixmap(scaled_pixmap)
        
        # --- UI Updates ---
        ready_text = f"READY ({self.engine.stable_frames}/{config.FACE_STABLE_FRAMES})" if self.engine.ready_to_start else f"WAITING ({self.engine.stable_frames}/{config.FACE_STABLE_FRAMES})"
        self.status_label.setText(f"Status: {ready_text}")
        if self.engine.ready_to_start:
            self.status_label.setStyleSheet("color: #66bb6a; font-weight: bold; font-size: 16px;")
        else:
            self.status_label.setStyleSheet("color: #ef5350; font-weight: bold; font-size: 16px;")
            
        self.left_ear_label.setText(f"Lewe Oko EAR: {self.engine.average_left_ear:.2f}")
        self.right_ear_label.setText(f"Prawe Oko EAR: {self.engine.average_right_ear:.2f}")
        
        if self.engine.is_eye_closed:
            self.is_closed_label.setText("Mrugnięcie: TAK (Oko zamknięte)")
            self.is_closed_label.setStyleSheet("color: #ef5350; font-weight: bold; font-size: 16px;")
        else:
            self.is_closed_label.setText("Mrugnięcie: NIE (Otwarte)")
            self.is_closed_label.setStyleSheet("color: #66bb6a; font-weight: bold; font-size: 16px;")
            
        # Text wrapping handled by QLabel.setWordWrap(True)
        self.seq_label.setText(f"Sekwencja:\n{self.engine.current_sequence}")
        self.text_label.setText(f"Tekst:\n{self.engine.decoded_text}")
        
        if self.engine.ready_to_start:
            pause_since = time.time() - self.engine.last_blink_end
            char_prog = min(pause_since / config.CHAR_PAUSE, 1.0) * 100
            word_prog = min(pause_since / config.WORD_PAUSE, 1.0) * 100
            self.char_bar.setValue(int(char_prog))
            self.word_bar.setValue(int(word_prog))
        else:
            self.char_bar.setValue(0)
            self.word_bar.setValue(0)

    def closeEvent(self, event):
        self.cap.release()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_stylesheet(app, theme='dark_teal.xml')
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
