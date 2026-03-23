import cv2
import mediapipe as mp
import numpy as np
import config

# TODO:
# face_mesh = mp_face_mesh.FaceMesh(
#     max_num_faces=1,
#     refine_landmarks=True,
#     min_detection_confidence=0.5,
#     min_tracking_confidence=0.5
# )

class EyeDetector:
    def __init__(self):
        self.face_mesh = mp.solutions.face_mesh.FaceMesh(refine_landmarks=True, min_detection_confidence=0.5)

    def calculate_ear(self, landmarks, w, h):
        return (self.eye_ratio(config.LEFT_EYE, landmarks, w, h) + self.eye_ratio(config.RIGHT_EYE, landmarks, w, h)) / 2.0

    def eye_ratio(self, indices, landmarks, w, h):
        pts = [np.array([landmarks[i].x * w, landmarks[i].y * h]) for i in indices]
        v1 = np.linalg.norm(pts[1] - pts[5])
        v2 = np.linalg.norm(pts[2] - pts[4])
        h1 = np.linalg.norm(pts[0] - pts[3])
        return (v1 + v2) / (2.0 * h1)

    def process(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return self.face_mesh.process(rgb)