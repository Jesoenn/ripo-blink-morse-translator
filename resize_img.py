import cv2
import os

INPUT_FOLDER = './test_imgs'
OUTPUT_FOLDER = './test_imgs/resize_50proc'
RESIZE_PERCENT = 50


def resize_image(img_path, scale_percent, output_path):
    img = cv2.imread(img_path)
    if img is None:
        print(f"Cannot read image: {img_path}")
        return False
    width = int(img.shape[1] * scale_percent / 100)
    height = int(img.shape[0] * scale_percent / 100)
    if width == 0 or height == 0:
        print(f"Too small percent or invalid image: {img_path}")
        return False
    dim = (width, height)
    resized = cv2.resize(img, dim, interpolation=cv2.INTER_AREA)
    cv2.imwrite(output_path, resized)
    return True


def main():
    if not os.path.isdir(INPUT_FOLDER):
        print(f"Input directory not found: {INPUT_FOLDER}")
        return
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    count = 0
    for fname in os.listdir(INPUT_FOLDER):
        if fname.lower().endswith('.jpg'):
            input_path = os.path.join(INPUT_FOLDER, fname)
            output_path = os.path.join(OUTPUT_FOLDER, fname)
            if resize_image(input_path, RESIZE_PERCENT, output_path):
                print(f"Resized: {fname}")
                count += 1
    print(f"Processed {count} files.")

if __name__ == "__main__":
    main()
