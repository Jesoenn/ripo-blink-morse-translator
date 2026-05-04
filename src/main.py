import sys
import cv2
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QLabel, QWidget,
                             QVBoxLayout, QHBoxLayout, QSlider, QFormLayout, QGroupBox, QProgressBar, QSizePolicy,
                             QFrame, QCheckBox, QScrollArea, QPushButton)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap

from image_utils import enhance_frame
from detector import EyeDetector
from engine import MorseEngine
import config
from qt_material import apply_stylesheet


class CameraWorker(QThread):
    update_signal = pyqtSignal(QImage, dict)

    def __init__(self):
        super().__init__()
        self.running = True
        self._clear_requested = False

    def request_clear(self):
        self._clear_requested = True

    def run(self):
        cap = cv2.VideoCapture(0)
        detector = EyeDetector()
        engine = MorseEngine()

        while self.running:
            if self._clear_requested:
                engine.clear_text()
                self._clear_requested = False

            ret, frame = cap.read()
            if not ret:
                continue

            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape

            # Preprocess frame
            processed = enhance_frame(frame)

            # Face detection
            results = detector.process(processed)

            is_looking = False
            left_ear_val, right_ear_val = 0.0, 0.0
            if results.multi_face_landmarks and config.ACTIVE:
                landmarks = results.multi_face_landmarks[0].landmark
                is_looking = detector.is_looking_at_camera(landmarks)
                if is_looking:
                    left_ear_val, right_ear_val = detector.calculate_ear_both_eyes(landmarks, w, h)
                    face_center, bbox = detector.face_center_and_bbox(landmarks, w, h)
                    engine.update(left_ear_val, right_ear_val, face_center=face_center, frame_size=(w, h))
                else:
                    engine.ready_to_start = False
                    engine.stable_frames = 0
            else:
                engine.stable_frames = 0
                engine.ready_to_start = False

            display_frame = processed if config.SHOW_PROCESSED_FACE else frame
            if config.SHOW_FACEMESH and results.multi_face_landmarks:
                detector.draw_facemesh(display_frame, results)

            rgb_image = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            h_img, w_img, ch = rgb_image.shape
            bytes_per_line = ch * w_img
            q_img = QImage(rgb_image.data, w_img, h_img, bytes_per_line, QImage.Format.Format_RGB888)
            q_img = q_img.copy()

            stats = {
                "is_looking": is_looking,
                "has_face": results.multi_face_landmarks is not None and config.ACTIVE,
                "ready_to_start": engine.ready_to_start,
                "stable_frames": engine.stable_frames,
                "average_left_ear": getattr(engine, 'average_left_ear', left_ear_val),
                "average_right_ear": getattr(engine, 'average_right_ear', right_ear_val),
                "is_eye_closed": engine.is_eye_closed,
                "current_sequence": engine.current_sequence,
                "decoded_text": engine.decoded_text,
                "last_blink_end": engine.last_blink_end
            }
            self.update_signal.emit(q_img, stats)
            self.msleep(10)
        cap.release()

    def stop(self):
        self.running = False
        self.wait()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Blink To Morse Translator")
        self.setMinimumSize(1000, 700)

        # Central Widget & Root Layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.root_layout = QVBoxLayout(self.central_widget)
        self.root_layout.setContentsMargins(20, 20, 20, 20)
        self.root_layout.setSpacing(15)

        # TOP: App Title
        self.title_label = QLabel("BLINK TO MORSE TRANSLATOR")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-size: 28px; font-weight: 900; color: #4db6ac; letter-spacing: 2px;")
        self.root_layout.addWidget(self.title_label)

        # MIDDLE: Left + Right panels
        self.content_layout = QHBoxLayout()
        self.root_layout.addLayout(self.content_layout)

        # ================= LEFT PANEL =================
        self.left_panel = QWidget()
        self.left_layout = QVBoxLayout(self.left_panel)
        self.left_layout.setContentsMargins(0, 0, 0, 0)
        self.left_layout.setSpacing(15)

        self.camera_row_layout = QHBoxLayout()
        self.camera_row_layout.setSpacing(10)

        # 1. Camera Box
        self.video_container = QFrame()
        self.video_container.setStyleSheet("background-color: #121212; border-radius: 12px; border: 2px solid #26a69a;")
        self.video_container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.video_container.setContentsMargins(2, 2, 2, 2)
        self.video_layout = QVBoxLayout(self.video_container)
        self.video_layout.setContentsMargins(2, 2, 2, 2)

        self.video_label = QLabel("Włączanie kamery...")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.video_label.setMinimumSize(320, 180)
        self.video_layout.addWidget(self.video_label)

        self.camera_row_layout.addWidget(self.video_container, stretch=5)

        # 2. Buttons
        self.btns_container = QVBoxLayout()
        self.btns_container.setSpacing(10)
        self.btns_container.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.btn_toggle = QPushButton("START")
        self.btn_toggle.setCheckable(True)
        self.btn_toggle.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.btn_toggle.setFixedHeight(50)
        self.btn_toggle.setStyleSheet("""
            QPushButton { 
                background-color: #263238; 
                font-weight: bold; 
                border: 1px solid #26a69a; 
                border-radius: 6px; 
                padding: 10px; 
            }
            QPushButton:hover { 
                background-color: #37474f; 
            }
            QPushButton:checked:pressed { 
                background-color: #1a2327; 
            }
            QPushButton:checked {
                background-color: #d32f2f; /* Ciemniejsza czerwień */
                border: 1px solid #ff5252;
            }
            QPushButton:checked:hover { 
                background-color: #ff5252; 
                border: 1px solid #ff8a80;
            }
            QPushButton:focus {
                border: 1px solid #4db6ac;
            }
            QPushButton:checked:focus {
                border: 1px solid #ff8a80;
            }
        """)
        self.btn_toggle.toggled.connect(self.toggle_active_state)

        self.btn_clear = QPushButton("Wyczyść")
        self.btn_clear.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.btn_clear.setFixedHeight(50)
        self.btn_clear.setStyleSheet("""
                    QPushButton { 
                        background-color: #263238; 
                        font-weight: bold; 
                        border: 1px solid #26a69a; 
                        border-radius: 6px; 
                        padding: 10px; 
                    }
                    QPushButton:focus { 
                        background-color: #263238; 
                        border: 1px solid #4db6ac; 
                    }
                    QPushButton:hover { 
                        background-color: #37474f; 
                    }
                    QPushButton:pressed { 
                        background-color: #1a2327; 
                    }
                """)
        self.btn_clear.clicked.connect(self.clear_engine_text)

        self.btns_container.addWidget(self.btn_toggle)
        self.btns_container.addWidget(self.btn_clear)

        self.camera_row_layout.addLayout(self.btns_container, stretch=1)
        self.left_layout.addLayout(self.camera_row_layout, stretch=1)

        # 3. Sequence panel
        self.seq_group = QGroupBox("Sekwencja Morse'a")
        self.seq_group.setFixedHeight(70)
        self.seq_group.setStyleSheet("QGroupBox { font-size: 14px; font-weight: bold; color: #80cbc4; }")
        self.seq_group_layout = QVBoxLayout()

        self.seq_label = QLabel(".._..")
        self.seq_label.setStyleSheet("font-size: 28px; color: #80cbc4; font-family: 'Courier New', monospace;")
        self.seq_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.seq_group_layout.addWidget(self.seq_label)
        self.seq_label.setMinimumHeight(15)
        self.seq_group.setLayout(self.seq_group_layout)
        self.left_layout.addWidget(self.seq_group)

        # 4. Text panel
        self.text_group = QGroupBox("Przetłumaczony Tekst")
        self.text_group.setStyleSheet("QGroupBox { font-size: 16px; font-weight: bold; color: #ffffff; }")
        self.text_layout = QVBoxLayout()

        self.text_label = QLabel("EXAMPLE")
        self.text_label.setStyleSheet("font-size: 38px; font-weight: bold; color: #ffffff;")
        self.text_label.setWordWrap(True)
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.text_label.setMinimumHeight(100)

        self.text_layout.addWidget(self.text_label)
        self.text_group.setLayout(self.text_layout)
        self.left_layout.addWidget(self.text_group)

        self.content_layout.addWidget(self.left_panel, stretch=1)

        # ================= RIGHT PANEL =================
        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout(self.right_panel)
        self.right_layout.setContentsMargins(15, 0, 15, 0)
        self.right_layout.setSpacing(20)

        # 1. Debug Info
        self.info_group = QGroupBox("Status Kamery i Twarzy")
        self.info_group.setStyleSheet("QGroupBox { font-size: 14px; font-weight: bold; }")
        self.info_layout = QVBoxLayout()
        self.info_layout.setSpacing(10)

        self.status_label = QLabel("Status: Czekaj")
        self.left_ear_label = QLabel("Lewe Oko: 0.00")
        self.right_ear_label = QLabel("Prawe Oko: 0.00")
        self.is_closed_label = QLabel("Mrugnięcie: NIE")

        for lbl in (self.status_label, self.left_ear_label, self.right_ear_label, self.is_closed_label):
            lbl.setStyleSheet("font-size: 16px;")
            self.info_layout.addWidget(lbl)

        self.info_group.setLayout(self.info_layout)
        self.right_layout.addWidget(self.info_group)

        # 2. Timing/Pauses
        self.pause_group = QGroupBox("Detekcja Przerwy")
        self.pause_group.setStyleSheet("QGroupBox { font-size: 14px; font-weight: bold; }")
        self.pause_layout = QVBoxLayout()
        self.pause_layout.setSpacing(15)

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
        self.sliders_group_layout = QVBoxLayout(self.sliders_group)

        self.sliders_scroll = QScrollArea()
        self.sliders_scroll.setWidgetResizable(True)
        self.sliders_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.sliders_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.sliders_content = QWidget()
        self.sliders_layout = QFormLayout(self.sliders_content)
        self.sliders_layout.setSpacing(12)

        self.dot_max_slider = QSlider(Qt.Orientation.Horizontal)
        self.dot_max_slider.setRange(50, 1500)
        self.dot_max_slider.setValue(int(config.DOT_MAX_TIME * 1000))
        self.dot_max_label = QLabel(f"{config.DOT_MAX_TIME * 1000:.0f} ms")
        self.dot_max_slider.valueChanged.connect(self.update_dot_max)
        self.sliders_layout.addRow("Max czas kropki:", self.dot_max_slider)
        self.sliders_layout.addRow("", self.dot_max_label)

        self.tol_slider = QSlider(Qt.Orientation.Horizontal)
        self.tol_slider.setRange(1, 300)
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
        self.sliders_layout.addRow("Zamykanie EAR < :", self.close_th_slider)
        self.sliders_layout.addRow("", self.close_th_label)

        self.open_th_slider = QSlider(Qt.Orientation.Horizontal)
        self.open_th_slider.setRange(5, 100)
        self.open_th_slider.setValue(int(config.BLINK_OPEN_THRESHOLD * 100))
        self.open_th_label = QLabel(f"{config.BLINK_OPEN_THRESHOLD:.2f}")
        self.open_th_slider.valueChanged.connect(self.update_open_th)
        self.sliders_layout.addRow("Otwieranie EAR > :", self.open_th_slider)
        self.sliders_layout.addRow("", self.open_th_label)



        # self.dash_min_slider = QSlider(Qt.Orientation.Horizontal)
        # self.dash_min_slider.setRange(100, 3000)
        # self.dash_min_slider.setValue(int(config.DASH_MIN_TIME * 1000))
        # self.dash_min_label = QLabel(f"{config.DASH_MIN_TIME * 1000:.0f} ms")
        # self.dash_min_slider.valueChanged.connect(self.update_dash_min)
        # self.sliders_layout.addRow("Min czas kreski:", self.dash_min_slider)
        # self.sliders_layout.addRow("", self.dash_min_label)

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

        self.sliders_scroll.setWidget(self.sliders_content)
        self.sliders_group_layout.addWidget(self.sliders_scroll)
        self.right_layout.addWidget(self.sliders_group, stretch=1)

        # 4. Toggles / Image Options
        self.toggles_group = QGroupBox("Opcje obrazu")
        self.toggles_group.setStyleSheet("QGroupBox { font-size: 14px; font-weight: bold; }")
        self.toggles_group_layout = QVBoxLayout(self.toggles_group)

        self.toggles_scroll = QScrollArea()
        self.toggles_scroll.setWidgetResizable(True)
        self.toggles_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.toggles_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.toggles_content = QWidget()
        self.toggles_layout = QVBoxLayout(self.toggles_content)
        self.toggles_layout.setSpacing(10)

        self.cb_clahe = QCheckBox("Poprawa kontrastu")
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

        self.cb_facemesh = QCheckBox("Pokaż siatkę twarzy")
        self.cb_facemesh.setChecked(config.SHOW_FACEMESH)
        self.cb_facemesh.stateChanged.connect(self.toggle_facemesh)
        self.toggles_layout.addWidget(self.cb_facemesh)

        self.cb_processed = QCheckBox("Pokaż przetworzoną twarz")
        self.cb_processed.setChecked(config.SHOW_PROCESSED_FACE)
        self.cb_processed.stateChanged.connect(self.toggle_processed)
        self.toggles_layout.addWidget(self.cb_processed)

        self.toggles_scroll.setWidget(self.toggles_content)
        self.toggles_group_layout.addWidget(self.toggles_scroll)
        self.right_layout.addWidget(self.toggles_group, stretch=1)

        self.right_layout.addStretch()
        self.content_layout.addWidget(self.right_panel)

        # Camera start in separate thread
        self.worker = CameraWorker()
        self.worker.update_signal.connect(self.update_ui)
        self.worker.start()

    # Settings - sliders, checkboxes
    def update_tol(self, value):
        val = max(value / 1000.0, 0.001)
        config.FACE_CENTER_TOLERANCE = val
        self.tol_label.setText(f"{val:.3f}")

    def toggle_active_state(self, checked):
        config.ACTIVE = checked
        if checked:
            self.btn_toggle.setText("STOP")
        else:
            self.btn_toggle.setText("START")

    def clear_engine_text(self):
        self.text_label.setText("")
        self.seq_label.setText("")
        self.worker.request_clear()

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

    # UI UPDATE
    def update_ui(self, q_img, stats):
        pixmap = QPixmap.fromImage(q_img)
        scaled_pixmap = pixmap.scaled(self.video_label.size(), Qt.AspectRatioMode.KeepAspectRatio,
                                      Qt.TransformationMode.SmoothTransformation)
        self.video_label.setPixmap(scaled_pixmap)
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if not stats['has_face']:
            self.status_label.setText("Status: Nie wykryto twarzy")
            self.status_label.setStyleSheet("color: #ff9800; font-weight: bold; font-size: 16px;")
        elif not stats['is_looking']:
            self.status_label.setText("Status: Patrz w kamerę")
            self.status_label.setStyleSheet("color: #ff1744; font-weight: bold; font-size: 16px;")
        else:
            ready_text = f"Gotowy" if stats[
                'ready_to_start'] else f"Czekaj ({stats['stable_frames']}/{config.FACE_STABLE_FRAMES})"
            self.status_label.setText(f"Status: {ready_text}")
            if stats['ready_to_start']:
                self.status_label.setStyleSheet("color: #66bb6a; font-weight: bold; font-size: 16px;")
            else:
                self.status_label.setStyleSheet("color: #ef5350; font-weight: bold; font-size: 16px;")

            self.left_ear_label.setText(f"Lewe Oko EAR: {stats['average_left_ear']:.2f}")
            self.right_ear_label.setText(f"Prawe Oko EAR: {stats['average_right_ear']:.2f}")

            if stats['is_eye_closed']:
                self.is_closed_label.setText("Mrugnięcie: TAK (Oko zamknięte)")
                self.is_closed_label.setStyleSheet("color: #ef5350; font-weight: bold; font-size: 16px;")
            else:
                self.is_closed_label.setText("Mrugnięcie: NIE (Oko otwarte)")
                self.is_closed_label.setStyleSheet("color: #66bb6a; font-weight: bold; font-size: 16px;")

            self.seq_label.setText(f"{stats['current_sequence']}")
            self.text_label.setText(f"{stats['decoded_text']}")

            if stats['ready_to_start']:
                pause_since = time.time() - stats['last_blink_end']
                min_time = max(pause_since-config.CHAR_PAUSE, 0.0)
                if (pause_since > config.CHAR_PAUSE + config.WORD_PAUSE):
                    min_time = 0
                word_prog = min(min_time / config.WORD_PAUSE, 1.0) * 100
                self.word_bar.setValue(int(word_prog))
            else:
                self.word_bar.setValue(0)


    def closeEvent(self, event):
        self.worker.stop()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_stylesheet(app, theme='dark_teal.xml')
    window = MainWindow()
    window.show()
    sys.exit(app.exec())