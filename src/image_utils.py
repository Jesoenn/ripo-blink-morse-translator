import cv2
import numpy as np
import math
import config


def apply_auto_gamma(gray, target_brightness=110):
    mean_brightness = np.mean(gray)
    if mean_brightness < 5 or mean_brightness > 250:
        return gray

    M = mean_brightness / 255.0
    T = target_brightness / 255.0
    gamma = math.log(T) / math.log(M)

    gamma = np.clip(gamma, config.GAMMA_MIN, config.GAMMA_MAX)
    table = np.array([((i / 255.0) ** gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
    return cv2.LUT(gray, table)

def apply_bilateral_filter(gray):
    return cv2.bilateralFilter(
        gray,
        config.BILATERAL_D,
        config.BILATERAL_SIGMA_COLOR,
        config.BILATERAL_SIGMA_SPACE
    )


def enhance_frame(frame):
    """
    RGB -> Gray -> Brightness -> CLAHE -> Bilateral -> RGB
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    if config.ENABLE_BRIGHTNESS_NORMALIZATION:
        gray = apply_auto_gamma(gray, target_brightness=config.BRIGHTNESS_TARGET)

    if config.ENABLE_CLAHE:
        clahe = cv2.createCLAHE(
            clipLimit=config.CLAHE_CLIP_LIMIT,
            tileGridSize=config.CLAHE_TILE_GRID
        )
        gray = clahe.apply(gray)


    if config.ENABLE_NOISE_REDUCTION:
        gray = apply_bilateral_filter(gray)

    # back to rgb - but in grayscale
    final_rgb = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    return final_rgb