import cv2
import os
import csv
from pathlib import Path
from detector import EyeDetector
from image_utils import enhance_frame
import config


class TestRunner:
    def __init__(self):
        self.detector = EyeDetector()
        self.results = []

    def classify_image(self, image_path):
        """
        Detect open/closed eyes, return EAR values for each eye
        """
        if not os.path.exists(image_path):
            print(f"Image not found: {image_path}")
            return None

        frame = cv2.imread(image_path)
        if frame is None:
            print(f"Cannot load image: {image_path}")
            return None

        h, w, _ = frame.shape

        # Preprocessing
        processed = enhance_frame(frame)

        # EAR
        results = self.detector.process(processed)
        if not results.multi_face_landmarks:
            return None

        landmarks = results.multi_face_landmarks[0].landmark

        # Check if looking at camera
        is_looking = self.detector.is_looking_at_camera(landmarks)
        if not is_looking:
            return "SIDE", 0.0, 0.0

        left_ear, right_ear = self.detector.calculate_ear_both_eyes(landmarks, w, h)

        #JEDNO OKO ZAMKNIETE TO closed. OBA MUSZA BYC OTWARTE
        is_closed = left_ear < config.BLINK_CLOSE_THRESHOLD or right_ear < config.BLINK_CLOSE_THRESHOLD

        classification = "CLOSED" if is_closed else "OPEN"
        return classification, left_ear, right_ear

    def run_tests(self):
        test_folder = config.TESTS_PATH
        results_file = os.path.join(test_folder, "tests_results.csv")
        image_extensions = ('.jpg', '.jpeg', '.png')

        # All images in given folder
        image_files = []
        if os.path.isdir(test_folder):
            for file in os.listdir(test_folder):
                if file.lower().endswith(image_extensions):
                    full_path = os.path.join(test_folder, file)
                    image_files.append((file, full_path))

        if not image_files:
            print(f"No images in folder: {test_folder}")
            return

        print(f"Found {len(image_files)} images.")

        results = []
        for filename, filepath in image_files:
            print(f"File: {filename}: ", end="")
            result = self.classify_image(filepath)

            # CLOSED/OPEN
            original_label = filename.split('_')[0] if '_' in filename else ''

            if result:
                classification, left_ear, right_ear = result
                print(f"OK - {classification}")

                is_correct = "YES" if classification == original_label else "NO"

                row = [
                    filename,
                    original_label,
                    classification,
                    is_correct,
                    "YES" if config.ENABLE_CLAHE else "NO",
                    "YES" if config.ENABLE_NOISE_REDUCTION else "NO",
                    "YES" if config.ENABLE_BRIGHTNESS_NORMALIZATION else "NO",
                    f"{left_ear:.4f}",
                    f"{right_ear:.4f}",
                    f"{config.BLINK_CLOSE_THRESHOLD:.4f}"
                ]
                results.append(row)
            else:
                print("Error - cannot read image.")

        # Save to CSV
        if results:
            try:
                file_exists = os.path.exists(results_file)
                write_header = not file_exists or os.stat(results_file).st_size == 0
                with open(results_file, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f, delimiter=';')
                    if write_header:
                        writer.writerow([
                            'Nazwa pliku',
                            'Oryginalna etykieta',
                            'Klasyfikacja',
                            'Poprawnosc',
                            'CLAHE',
                            'NOISE REDUCTION',
                            'NORMALIZACJA JASNOSCI',
                            'Left EAR',
                            'Right EAR',
                            'EAR threshold'
                        ])
                    writer.writerows(results)

                print(f"\nResults in file: {results_file}")
            except Exception as e:
                print(f"Error while saving results to csv: {e}")


def run_tests():
    print("\nStarting tests...")
    classifier = TestRunner()
    classifier.run_tests()
    print("Tests finished\n")

if __name__ == "__main__":
    run_tests()