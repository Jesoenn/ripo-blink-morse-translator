import threading
import time
import config
from morse_data import MorseTranslator
from autocorrect import Autocorrector


class MorseEngine:
    def __init__(self):
        self.current_sequence = ""
        self.decoded_text = ""
        self.is_eye_closed = False
        self.last_state_change = time.time()
        self.pause_processed = True
        self.char_pause_processed = False
        self.last_blink_end = time.time()  # time when eyes last opened (end of blink)
        # Hysteresis state (preventing oscillation)
        self.eye_open_hysteresis = True  # True=open, False=closed (but filtering)

        self.left_ear_history = []
        self.current_left_ear = 0.0
        self.average_left_ear = 0.0
        self.left_eye_closed = False

        self.right_ear_history = []
        self.current_right_ear = 0.0
        self.average_right_ear = 0.0
        self.right_eye_closed = False
        # Face / readiness
        self.face_center_history = []
        self.stable_frames = 0
        self.ready_to_start = False

        # Autocorrector (simple prototype)
        try:
            self.autocorrector = Autocorrector(language='pl', debug=True)
        except Exception as e:
            print(f"[MorseEngine] Failed to init autocorrector: {e}")
            self.autocorrector = None

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

    def update(self, left_ear, right_ear, face_center=None, frame_size=None):
        self.update_left_ear_average(left_ear)
        self.update_right_ear_average(right_ear)

        now = time.time()
        duration = now - self.last_state_change

        # Update face stability / readiness
        if face_center and frame_size:
            w, h = frame_size
            norm = (face_center[0] / w, face_center[1] / h)
            self.face_center_history.append(norm)
            if len(self.face_center_history) > config.FACE_STABLE_FRAMES:
                self.face_center_history.pop(0)

            # compute max displacement from mean
            mean_x = sum([c[0] for c in self.face_center_history]) / len(self.face_center_history)
            mean_y = sum([c[1] for c in self.face_center_history]) / len(self.face_center_history)
            max_disp = 0.0
            for c in self.face_center_history:
                dx = c[0] - mean_x
                dy = c[1] - mean_y
                disp = (dx * dx + dy * dy) ** 0.5
                if disp > max_disp:
                    max_disp = disp

            if max_disp < config.FACE_CENTER_TOLERANCE:
                if self.stable_frames <= config.FACE_STABLE_FRAMES:
                    self.stable_frames += 1
            # Face movement, reset
            else:
                self.stable_frames = 0
                if self.ready_to_start:
                    self.ready_to_start = False

            if not self.ready_to_start and self.stable_frames >= config.FACE_STABLE_FRAMES:
                self.ready_to_start = True

        # NIE DZIAŁA
        # # If one eye is always very low/high, assume it's not visible -> use only other eye
        # # Mark eye as "not available" if EAR stays in extreme range
        # left_available = 0.05 < self.average_left_ear < 1.5
        # right_available = 0.05 < self.average_right_ear < 1.5
        
        # # Determine which eyes are closed using close threshold
        # if left_available and right_available:
        #     left_closed = self.average_left_ear < config.BLINK_CLOSE_THRESHOLD
        #     right_closed = self.average_right_ear < config.BLINK_CLOSE_THRESHOLD
        #     eyes_closed_raw = left_closed and right_closed
        # elif left_available:
        #     eyes_closed_raw = self.average_left_ear < config.BLINK_CLOSE_THRESHOLD
        # elif right_available:
        #     eyes_closed_raw = self.average_right_ear < config.BLINK_CLOSE_THRESHOLD
        # else:
        #     eyes_closed_raw = False

        left_closed = self.average_left_ear < config.BLINK_CLOSE_THRESHOLD
        right_closed = self.average_right_ear < config.BLINK_CLOSE_THRESHOLD
        eyes_closed_raw = left_closed and right_closed

        # Apply hysteresis to prevent bouncing between closed and open
        if not self.eye_open_hysteresis:
            # Currently in CLOSED state - require higher threshold to open
            eyes_are_opening = False
            if self.current_left_ear > config.BLINK_OPEN_THRESHOLD:
                eyes_are_opening = True
                # print(f"[DEBUG] Left eye opening: EAR={self.current_left_ear:.2f} > {config.BLINK_OPEN_THRESHOLD}")
            if self.current_right_ear > config.BLINK_OPEN_THRESHOLD:
                eyes_are_opening = True
                # print(f"[DEBUG] Right eye opening: EAR={self.current_right_ear:.2f} > {config.BLINK_OPEN_THRESHOLD}")
            if eyes_are_opening:
                self.eye_open_hysteresis = True
                both_eyes_closed = False
            else:
                # Stay closed
                both_eyes_closed = True and self.ready_to_start
        else:
            # Currently in OPEN state - close on low threshold (using average EAR for stability)
            if eyes_closed_raw:
                self.eye_open_hysteresis = False
                both_eyes_closed = True and self.ready_to_start
            else:
                both_eyes_closed = False

        if both_eyes_closed:
            if not self.is_eye_closed:
                self.is_eye_closed = True
                self.last_state_change = now
                self.pause_processed = False
                self.char_pause_processed = False
        else:
            if self.is_eye_closed:
                # Eye just opened - Blink completed
                self.is_eye_closed = False
                blink_duration = duration
                # Filter out too short or too long blinks
                if blink_duration < config.MIN_BLINK_DURATION:
                    # ignore as noise
                    pass
                elif blink_duration > config.MAX_BLINK_DURATION:
                    # ignore very long holds as unintended
                    pass
                else:
                    if blink_duration <= config.DOT_MAX_TIME:
                        self.current_sequence += "."
                    else:
                        self.current_sequence += "-"
                self.last_state_change = now
                self.last_blink_end = now  # update last blink end time
                self.pause_processed = False  # Reset pause for next sequence
                self.char_pause_processed = False

        # Check pause time (poza blokami otwierania/zamykania oczu)
        # Ta logika powinna się zawsze wykonywać gdy oczy są otwarte i nie ruszamy się
        if not both_eyes_closed and self.ready_to_start and not self.pause_processed:
            pause_since_blink = now - self.last_blink_end
            # word + char. Time starts after char finished
            if pause_since_blink > config.WORD_PAUSE + config.CHAR_PAUSE:
                # finalize character, insert space, and autocorrect last word
                self.finalize_char()
                if self.autocorrector:
                    self._autocorrect_last_word()
                if self.decoded_text and not self.decoded_text.endswith(' '):
                    self.decoded_text += ' '
                self.pause_processed = True
                self.char_pause_processed = True
            elif pause_since_blink > config.CHAR_PAUSE and not self.char_pause_processed:
                self.finalize_char()
                self.char_pause_processed = True

    def finalize_char(self):
        if self.current_sequence:
            decoded_char = MorseTranslator.translate(self.current_sequence)
            if decoded_char == "-":
                self.decoded_text = self.decoded_text[:-1]  # Remove last symbol
            elif decoded_char == " " and self.decoded_text[-1:] != " ":
                self.decoded_text += " "
            elif decoded_char != "?":
                self.decoded_text += decoded_char
            self.current_sequence = ""

    def _autocorrect_last_word(self):
        if not self.autocorrector:
            return
        if not self.decoded_text or not self.decoded_text.strip():
            return
        # get the last word (everything after last space) - no race condition
        full_text_at_start = self.decoded_text
        last_space_idx = full_text_at_start.rfind(' ')
        if last_space_idx == -1:
            # no space found - entire text is one word
            last_word = self.decoded_text
            prefix = ''
        else:
            prefix = full_text_at_start[:last_space_idx + 1]
            last_word = full_text_at_start[last_space_idx + 1:]

        def run_correction(word_to_correct, text_prefix, original_full_text=full_text_at_start):
            corrected = self.autocorrector.correct_text(word_to_correct)

            if corrected and corrected != word_to_correct:
                # if no new letter was added since correction
                if self.decoded_text == original_full_text:
                    self.decoded_text = text_prefix + corrected
                else:
                    # Save what was added during thread execution, replace only corrected word
                    new_extension = self.decoded_text[len(original_full_text):]
                    self.decoded_text = text_prefix + corrected + new_extension

        threading.Thread(target=run_correction, args=(last_word, prefix), daemon=True).start()

    def clear_text(self):
        self.decoded_text = ""
        self.current_sequence = ""