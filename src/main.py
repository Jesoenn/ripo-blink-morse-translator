import cv2
from image_utils import enhance_frame
from detector import EyeDetector
from engine import MorseEngine
from ui import UI


def main():
    cap = cv2.VideoCapture(0)
    detector = EyeDetector()
    engine = MorseEngine()
    ui = UI()

    # Do while camera is working
    while cap.isOpened():
        frameReceived, frame = cap.read()
        if not frameReceived:
            break

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        # 1. Preprocess frame - enhance
        processed = enhance_frame(frame)

        # 2. Detect face
        results = detector.process(processed)
        ear = 0.0

        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0].landmark
            ear = detector.calculate_ear(landmarks, w, h)

            # 3. Check if blink based on ear
            engine.update(ear)

        # 4. Render
        ui.render(frame, ear, engine)

        # Exit - ESC
        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    ui.close()


if __name__ == "__main__":
    main()