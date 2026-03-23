import cv2
import config


class UI:
    def __init__(self):
        self.window_name = "Blink To Morse Translator"

    def draw_debug_info(self, frame, ear, is_eye_closed):
        # Eye opened/closed
        color = config.COLOR_EAR_CLOSED if is_eye_closed else config.COLOR_EAR_OPEN
        status_text = "CLOSED" if is_eye_closed else "OPENED"
        # EAR ratio
        cv2.putText(frame, f"EAR: {ear:.2f} ({status_text})", config.POS_EAR,
                    cv2.FONT_HERSHEY_SIMPLEX, config.FONT_SCALE_SMALL, color, config.FONT_THICKNESS)

    def draw_morse_data(self, frame, current_sequence, decoded_text):
        cv2.putText(frame, f"Sequence: {current_sequence}", config.POS_SEQ,
                    cv2.FONT_HERSHEY_SIMPLEX, config.FONT_SCALE_SMALL, config.COLOR_SEQ, config.FONT_THICKNESS)

        cv2.putText(frame, f"Text: {decoded_text}", config.POS_TEXT,
                    cv2.FONT_HERSHEY_SIMPLEX, config.FONT_SCALE_LARGE, config.COLOR_TEXT, config.FONT_THICKNESS)

    def render(self, frame, ear, engine):
        self.draw_debug_info(frame, ear, engine.is_eye_closed)
        self.draw_morse_data(frame, engine.current_sequence, engine.decoded_text)

        cv2.imshow(self.window_name, frame)

    def close(self):
        cv2.destroyAllWindows()