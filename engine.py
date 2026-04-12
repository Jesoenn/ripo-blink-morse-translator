import time
import config
from morse_data import MorseTranslator


class MorseEngine:
    def __init__(self):
        self.current_sequence = ""
        self.decoded_text = ""
        self.is_eye_closed = False
        self.last_state_change = time.time()
        self.pause_processed = True

        self.left_ear_history = []
        self.current_left_ear = 0.0
        self.average_left_ear = 0.0
        self.left_eye_closed = False

        self.right_ear_history = []
        self.current_right_ear = 0.0
        self.average_right_ear = 0.0
        self.right_eye_closed = False

    # Use 3 recent values to calculate average EAR for left eye
    def update_left_ear_average(self, ear):
        self.current_left_ear = ear
        self.left_ear_history.append(ear)

        if len(self.left_ear_history) > 3:
            self.left_ear_history.pop(0)

        self.average_left_ear = sum(self.left_ear_history) / len(self.left_ear_history)

    # Use 3 recent values to calculate average EAR for right eye
    def update_right_ear_average(self, ear):
        self.current_right_ear = ear
        self.right_ear_history.append(ear)

        if len(self.right_ear_history) > 3:
            self.right_ear_history.pop(0)

        self.average_right_ear = sum(self.right_ear_history) / len(self.right_ear_history)

    def update(self, left_ear, right_ear):
        self.update_left_ear_average(left_ear)
        self.update_right_ear_average(right_ear)

        now = time.time()
        duration = now - self.last_state_change

        left_closed = self.average_left_ear < config.BLINK_THRESHOLD
        right_closed = self.average_right_ear < config.BLINK_THRESHOLD

        both_eyes_closed = left_closed and right_closed

        if both_eyes_closed:
            if not self.is_eye_closed:
                self.is_eye_closed = True
                self.last_state_change = now
                self.pause_processed = False
        else:
            if self.is_eye_closed:
                # Eye just opened - Blink completed
                self.is_eye_closed = False
                if duration < config.DOT_MAX_TIME:
                    self.current_sequence += "."
                elif duration > config.TEXT_CLEAR:
                    self.decoded_text = ""
                    self.current_sequence = ""
                    self.pause_processed = True
                else:
                    self.current_sequence += "-"
                self.last_state_change = now

            # End of letter/word
            if not self.pause_processed:
                if duration > config.CHAR_PAUSE:
                    self.finalize_char()
                    self.pause_processed = True

    def finalize_char(self):
        if self.current_sequence:
            decoded_char = MorseTranslator.translate(self.current_sequence)
            if decoded_char == "-":
                self.decoded_text = self.decoded_text[:-1]  # Remove last symbol
            elif decoded_char != "?":
                self.decoded_text += decoded_char
            self.current_sequence = ""