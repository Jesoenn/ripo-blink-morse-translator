import cv2
import os
import sys
import src.config as config

def get_next_index(folder, prefix):
    """Find max index of existing files"""
    max_idx = 0
    for fname in os.listdir(folder):
        if fname.startswith(prefix) and fname.endswith('.jpg'):
            try:
                idx = int(fname[len(prefix)+1:-4])
                if idx > max_idx:
                    max_idx = idx
            except ValueError:
                continue
    return max_idx + 1

def main():
    folder = os.path.abspath(os.path.join(os.path.dirname(__file__), config.SAVE_IMG))
    os.makedirs(folder, exist_ok=True)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Cannot open camera.")
        return

    print(f"Lewa strzalka: Zapisz jako CLOSED\nPrawa strzalka: Zapisz jako OPEN\nESC: Wyjdz")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error reading camera.")
            break
        frame = cv2.flip(frame, 1)
        cv2.imshow("Camera", frame)
        key = cv2.waitKeyEx(1)
        # ESC
        if key == 27:
            break
        # LEFT ARROW
        elif key == 2424832:
            idx = get_next_index(folder, "CLOSED")
            fname = f"CLOSED_{idx}.jpg"
            cv2.imwrite(os.path.join(folder, fname), frame)
            print(f"Saved file to: {fname}")
        # RIGHT ARROW
        elif key == 2555904:
            idx = get_next_index(folder, "OPEN")
            fname = f"OPEN_{idx}.jpg"
            cv2.imwrite(os.path.join(folder, fname), frame)
            print(f"Saved file to: {fname}")

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()


