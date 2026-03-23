# ========================================
# image_utils.py
# ========================================
SHOW_POSTPROCESSING_PLOT = False

# ========================================
# engine.py
# MorseEngine - translate blinks to symbols
# ========================================
BLINK_THRESHOLD = 0.18  # EAR THRESHOLD   0.20??
DOT_MAX_TIME = 0.4
DASH_MIN_TIME = 0.5
CHAR_PAUSE = 1.0
WORD_PAUSE = 2.0

# ========================================
# detector.py
# EyeDetector - eye landmark indexes
# ========================================
LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]

# ========================================
# ui.py
# Colors in BGR
# ========================================
COLOR_EAR_OPEN = (0, 255, 0)   # Green
COLOR_EAR_CLOSED = (0, 0, 255) # Red
COLOR_SEQ = (255, 255, 0)      # Yellow
COLOR_TEXT = (255, 255, 255)   # White

POS_EAR = (20, 40)
POS_SEQ = (20, 90)
POS_TEXT = (20, 150)

# Fonts
FONT_SCALE_SMALL = 0.8
FONT_SCALE_LARGE = 1.2
FONT_THICKNESS = 2

