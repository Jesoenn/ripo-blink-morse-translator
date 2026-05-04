import cv2
import numpy as np
import math
import config


def apply_auto_gamma(channel, target_brightness=110):
    mean_brightness = np.mean(channel)
    if mean_brightness < 5 or mean_brightness > 250:
        return channel

    M = mean_brightness / 255.0
    T = target_brightness / 255.0
    gamma = math.log(T) / math.log(M)

    gamma = np.clip(gamma, config.GAMMA_MIN, config.GAMMA_MAX)
    table = np.array([((i / 255.0) ** gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
    return cv2.LUT(channel, table)


def apply_bilateral_filter(channel):
    return cv2.bilateralFilter(
        channel,
        config.BILATERAL_D,
        config.BILATERAL_SIGMA_COLOR,
        config.BILATERAL_SIGMA_SPACE
    )


def enhance_frame(frame):
    """
    BGR -> LAB -> Enhance L channel -> BGR
    """
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    if config.ENABLE_BRIGHTNESS_NORMALIZATION:
        l = apply_auto_gamma(l, target_brightness=config.BRIGHTNESS_TARGET)

    if config.ENABLE_CLAHE:
        clahe = cv2.createCLAHE(
            clipLimit=config.CLAHE_CLIP_LIMIT,
            tileGridSize=config.CLAHE_TILE_GRID
        )
        l = clahe.apply(l)

    if config.ENABLE_NOISE_REDUCTION:
        l = apply_bilateral_filter(l)

    enhanced_lab = cv2.merge((l, a, b))
    final_bgr = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)

    return final_bgr