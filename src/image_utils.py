import cv2
import matplotlib.pyplot as plt
import config



def enhance_frame(frame):
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    enhanced = cv2.cvtColor(cv2.merge((cl, a, b)), cv2.COLOR_LAB2BGR)

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