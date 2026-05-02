import cv2
import config


class UI:
    def __init__(self):
        self.window_name = "Blink To Morse Translator"
        cv2.namedWindow(self.window_name)
        # create trackbars for tuning
        self._create_trackbars()

    def draw_debug_info(self, frame, left_ear, right_ear, is_eye_closed):
        # Eye opened/closed
        color = config.COLOR_EAR_CLOSED if is_eye_closed else config.COLOR_EAR_OPEN
        status_text = "CLOSED" if is_eye_closed else "OPENED"
        # Left eye EAR
        cv2.putText(frame, f"Left EAR: {left_ear:.2f}", config.POS_EAR,
                    cv2.FONT_HERSHEY_SIMPLEX, config.FONT_SCALE_SMALL, config.COLOR_EAR_OPEN, config.FONT_THICKNESS)
        # Right eye EAR
        cv2.putText(frame, f"Right EAR: {right_ear:.2f}", (config.POS_EAR[0], config.POS_EAR[1] + 30),
                    cv2.FONT_HERSHEY_SIMPLEX, config.FONT_SCALE_SMALL, config.COLOR_EAR_OPEN, config.FONT_THICKNESS)
        # Status
        cv2.putText(frame, f"Status: {status_text}", (config.POS_EAR[0], config.POS_EAR[1] + 60),
                    cv2.FONT_HERSHEY_SIMPLEX, config.FONT_SCALE_SMALL, color, config.FONT_THICKNESS)

    def draw_morse_data(self, frame, current_sequence, decoded_text):
        cv2.putText(frame, f"Sequence: {current_sequence}", config.POS_SEQ,
                    cv2.FONT_HERSHEY_SIMPLEX, config.FONT_SCALE_SMALL, config.COLOR_SEQ, config.FONT_THICKNESS)

        cv2.putText(frame, f"Text: {decoded_text}", config.POS_TEXT,
                    cv2.FONT_HERSHEY_SIMPLEX, config.FONT_SCALE_LARGE, config.COLOR_TEXT, config.FONT_THICKNESS)

    def render(self, frame, engine):
        # read trackbar values and update config
        self._read_trackbars()

        self.draw_debug_info(frame, engine.average_left_ear, engine.average_right_ear, engine.is_eye_closed)
        self.draw_morse_data(frame, engine.current_sequence, engine.decoded_text)
        
        # Draw readiness status
        import time
        readiness_color = (0, 255, 0) if engine.ready_to_start else (0, 0, 255)
        readiness_text = f"READY ({engine.stable_frames}/{config.FACE_STABLE_FRAMES})" if engine.ready_to_start else f"WAITING ({engine.stable_frames}/{config.FACE_STABLE_FRAMES})"
        cv2.putText(frame, readiness_text, (20, 295), cv2.FONT_HERSHEY_SIMPLEX, 0.8, readiness_color, 2)
        
        # Draw pause timer (time since last blink)
        if engine.ready_to_start:
            pause_since_blink = time.time() - engine.last_blink_end
            char_pause_progress = min(pause_since_blink / config.CHAR_PAUSE, 1.0)
            word_pause_progress = min(pause_since_blink / config.WORD_PAUSE, 1.0)
            
            # Visual progress bars
            bar_width = 200
            bar_height = 10
            bar_x, bar_y = 20, 320
            
            # Character pause bar (1 second)
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + int(bar_width * char_pause_progress), bar_y + bar_height),
                         (255, 255, 0), -1)  # Yellow
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (255, 255, 0), 2)
            cv2.putText(frame, f"CHAR: {pause_since_blink:.1f}s / {config.CHAR_PAUSE}s", (bar_x + bar_width + 10, bar_y + 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 1)
            
            # Word pause bar (2 seconds)
            bar_y_word = bar_y + 20
            cv2.rectangle(frame, (bar_x, bar_y_word), (bar_x + int(bar_width * word_pause_progress), bar_y_word + bar_height),
                         (0, 255, 255), -1)  # Cyan
            cv2.rectangle(frame, (bar_x, bar_y_word), (bar_x + bar_width, bar_y_word + bar_height), (0, 255, 255), 2)
            cv2.putText(frame, f"WORD: {pause_since_blink:.1f}s / {config.WORD_PAUSE}s", (bar_x + bar_width + 10, bar_y_word + 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1)
        
        # draw current tuning values
        cv2.putText(frame, f"min_blink(ms): {int(config.MIN_BLINK_DURATION*1000)}", (20, 375), cv2.FONT_HERSHEY_SIMPLEX, 0.6, config.COLOR_TEXT, 2)
        cv2.putText(frame, f"max_blink(ms): {int(config.MAX_BLINK_DURATION*1000)}", (20, 395), cv2.FONT_HERSHEY_SIMPLEX, 0.6, config.COLOR_TEXT, 2)
        cv2.putText(frame, f"face_tol: {config.FACE_CENTER_TOLERANCE:.3f}", (20, 415), cv2.FONT_HERSHEY_SIMPLEX, 0.6, config.COLOR_TEXT, 2)

        cv2.imshow(self.window_name, frame)

    def close(self):
        cv2.destroyAllWindows()

    def _create_trackbars(self):
        # MIN_BLINK_DURATION: 10ms - 500ms
        cv2.createTrackbar('min_blink_ms', self.window_name, int(config.MIN_BLINK_DURATION*1000), 500, lambda v: None)
        # MAX_BLINK_DURATION: 300ms - 3000ms
        cv2.createTrackbar('max_blink_ms', self.window_name, int(config.MAX_BLINK_DURATION*1000), 3000, lambda v: None)
        # FACE_CENTER_TOLERANCE: 0.01 - 0.50 (stored as int 1-500)
        cv2.createTrackbar('face_tol_x1000', self.window_name, int(config.FACE_CENTER_TOLERANCE*1000), 500, lambda v: None)

    def _read_trackbars(self):
        try:
            min_ms = cv2.getTrackbarPos('min_blink_ms', self.window_name)
            max_ms = cv2.getTrackbarPos('max_blink_ms', self.window_name)
            tol = cv2.getTrackbarPos('face_tol_x1000', self.window_name)
            # sanitize
            if min_ms < 1:
                min_ms = 1
            if max_ms < min_ms:
                max_ms = min_ms
            config.MIN_BLINK_DURATION = max(min_ms / 1000.0, 0.001)
            config.MAX_BLINK_DURATION = max_ms / 1000.0
            config.FACE_CENTER_TOLERANCE = max(tol / 1000.0, 0.001)
        except Exception:
            pass