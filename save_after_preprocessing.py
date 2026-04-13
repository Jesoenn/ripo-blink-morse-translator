import cv2
import os
import src.config as config
import src.image_utils as image_utils

FILENAMES = [
    "OPEN_14.jpg",
]

def main():
    input_dir = os.path.abspath(config.TESTS_PATH)
    for fname in FILENAMES:
        input_path = os.path.join(input_dir, fname)
        if not os.path.exists(input_path):
            print(f"File not found: {input_path}")
            continue
        img = cv2.imread(input_path)
        if img is None:
            print(f"Cannot load image: {input_path}")
            continue
        processed = image_utils.enhance_frame(img)
        out_name = f"_AFTER_{fname}"
        out_path = os.path.join(input_dir, out_name)
        cv2.imwrite(out_path, processed)
        print(f"Saved to file: {out_path}")

if __name__ == "__main__":
    main()

