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

    def update(self, ear):
        now = time.time()
        duration = now - self.last_state_change

        if ear < config.BLINK_THRESHOLD:
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
                else:
                    self.current_sequence += "-"
                self.last_state_change = now


            # End of letter/word
            if not self.pause_processed:
                if duration > config.WORD_PAUSE:
                    self.finalize_char()
                    self.decoded_text += " "
                    self.pause_processed = True
                elif duration > config.CHAR_PAUSE:
                    self.finalize_char()
                    self.pause_processed = True

    def finalize_char(self):
        if self.current_sequence:
            self.decoded_text += MorseTranslator.translate(self.current_sequence)
            self.current_sequence = ""