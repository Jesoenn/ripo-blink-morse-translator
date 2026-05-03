# ========================================
# Tests
# ========================================
# Domyślnie uruchamiamy aplikację (kamera). Ustaw na True by uruchomić testy.
ENABLE_TESTS = False
TESTS_PATH = "./test_imgs/"
SAVE_IMG = "./test_imgs/"

# ========================================
# image_utils.py
# ========================================
ENABLE_BRIGHTNESS_NORMALIZATION = True
BRIGHTNESS_TARGET = 120
GAMMA_MIN = 0.4          # Lowest brightness during day
GAMMA_MAX = 2.5          # Max brightness during night

ENABLE_CLAHE = True
CLAHE_CLIP_LIMIT = 3.0
CLAHE_TILE_GRID = (8, 8)

ENABLE_NOISE_REDUCTION = True
BILATERAL_D = 3
BILATERAL_SIGMA_COLOR = 25
BILATERAL_SIGMA_SPACE = 25

# ========================================
# Camera display
# ========================================
SHOW_FACEMESH = False
SHOW_PROCESSED_FACE = True

# ========================================
# engine.py
# MorseEngine - translate blinks to symbols
# ========================================
# Hysteresis thresholds to prevent oscillation
BLINK_CLOSE_THRESHOLD = 0.15   # EAR poniżej tego = oczy zamykają się
BLINK_OPEN_THRESHOLD = 0.20    # EAR powyżej tego = oczy otwierają się (zapobiega oscylacji)
DOT_MAX_TIME = 0.4
DASH_MIN_TIME = 0.5
CHAR_PAUSE = 1.0
WORD_PAUSE = 2.0
TEXT_CLEAR = 3.0
MIN_BLINK_DURATION = 0.05  # Minimalny czas mrugnięcia w sekundach (filtrowanie szumów)
MAX_BLINK_DURATION = 1.2   # Maksymalny czas mrugnięcia w sekundach (przeciwdziała zbyt długim przytrzymaniom)

# Face / start position
FACE_STABLE_FRAMES = 20        # Stable for given time before starting blink detection
FACE_CENTER_TOLERANCE = 0.07

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
POS_SEQ = (20, 130)
POS_TEXT = (20, 170)

# Fonts
FONT_SCALE_SMALL = 0.8
FONT_SCALE_LARGE = 1.2
FONT_THICKNESS = 2

