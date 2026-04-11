import cv2
import config


class UI:
    def __init__(self):
        self.window_name = "Blink To Morse Translator"

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
        self.draw_debug_info(frame, engine.average_left_ear, engine.average_right_ear, engine.is_eye_closed)
        self.draw_morse_data(frame, engine.current_sequence, engine.decoded_text)

        cv2.imshow(self.window_name, frame)

    def close(self):
        cv2.destroyAllWindows()