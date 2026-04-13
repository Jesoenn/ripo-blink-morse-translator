import cv2
import matplotlib.pyplot as plt
import numpy as np
import config

def apply_gamma_correction(frame, gamma):
    inv_gamma = 1.0 / gamma
    table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
    return cv2.LUT(frame, table)


def apply_noise_reduction(frame):
    return cv2.GaussianBlur(frame, (3, 3), 0)


def normalize_brightness(frame):
    target = config.BRIGHTNESS_TARGET
    
    # Convert to LAB color space
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    mean_brightness = np.mean(l)
    if mean_brightness > 0:
        adjustment = target / mean_brightness
    else:
        adjustment = 1.0
    
    # Apply adjustment (clamp values to 0-255)
    l = np.clip(l * adjustment, 0, 255).astype(np.uint8)
    
    # Merge back and convert to BGR
    lab_adjusted = cv2.merge((l, a, b))
    return cv2.cvtColor(lab_adjusted, cv2.COLOR_LAB2BGR)


def apply_clahe(frame):
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(
        clipLimit=config.CLAHE_CLIP_LIMIT,
        tileGridSize=config.CLAHE_TILE_GRID
    )
    cl = clahe.apply(l)
    return cv2.cvtColor(cv2.merge((cl, a, b)), cv2.COLOR_LAB2BGR)


def enhance_frame(frame):
    enhanced = frame.copy()
    
    # Noise reduction
    if config.ENABLE_NOISE_REDUCTION:
        enhanced = apply_noise_reduction(enhanced)
    
    # Brightness normalization
    if config.ENABLE_BRIGHTNESS_NORMALIZATION:
        enhanced = normalize_brightness(enhanced)
    
    # Gamma correction
    if config.ENABLE_GAMMA_CORRECTION:
        enhanced = apply_gamma_correction(enhanced, config.GAMMA_VALUE)
    
    # Apply CLAHE
    if config.ENABLE_CLAHE:
        enhanced = apply_clahe(enhanced)

    if config.SHOW_POSTPROCESSING_PLOT:
        show_plot(frame, enhanced)

    return enhanced

def show_plot(original, enhanced):
    fig, axes = plt.subplots(1, 2, figsize=(12, 6))

    axes[0].imshow(cv2.cvtColor(original, cv2.COLOR_BGR2RGB))
    axes[0].set_title("Original")
    axes[0].axis('off')

    axes[1].imshow(cv2.cvtColor(enhanced, cv2.COLOR_BGR2RGB))
    axes[1].set_title("CLAHE")
    axes[1].axis('off')

    plt.show()
    print("Press space...")
    input()
    plt.close(fig)

    return enhanced
