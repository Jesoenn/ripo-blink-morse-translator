import cv2
import mediapipe as mp
import numpy as np
import config

class EyeDetector:
    def __init__(self):
        self.face_mesh = mp.solutions.face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True, min_detection_confidence=0.5, min_tracking_confidence=0.5)

    def calculate_ear(self, landmarks, w, h):
        return (self.eye_ratio(config.LEFT_EYE, landmarks, w, h) + self.eye_ratio(config.RIGHT_EYE, landmarks, w, h)) / 2.0

    def calculate_ear_both_eyes(self, landmarks, w, h):
        left_ear = self.eye_ratio(config.LEFT_EYE, landmarks, w, h)
        right_ear = self.eye_ratio(config.RIGHT_EYE, landmarks, w, h)
        return left_ear, right_ear

    def eye_ratio(self, indices, landmarks, w, h):
        pts = [np.array([landmarks[i].x * w, landmarks[i].y * h]) for i in indices]
        v1 = np.linalg.norm(pts[1] - pts[5])
        v2 = np.linalg.norm(pts[2] - pts[4])
        h1 = np.linalg.norm(pts[0] - pts[3])
        return (v1 + v2) / (2.0 * h1)

    def process(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return self.face_mesh.process(rgb)

    def draw_facemesh(self, frame, results):
        if not results.multi_face_landmarks:
            return
        for face_landmarks in results.multi_face_landmarks:
            mp.solutions.drawing_utils.draw_landmarks(
                frame,
                face_landmarks,
                mp.solutions.face_mesh.FACEMESH_TESSELATION,
                landmark_drawing_spec=None,
                connection_drawing_spec=mp.solutions.drawing_styles.get_default_face_mesh_tesselation_style()
            )

    def face_center_and_bbox(self, landmarks, w, h):
        xs = [landmarks[i].x * w for i in range(len(landmarks))]
        ys = [landmarks[i].y * h for i in range(len(landmarks))]
        minx, maxx = min(xs), max(xs)
        miny, maxy = min(ys), max(ys)
        cx = (minx + maxx) / 2.0
        cy = (miny + maxy) / 2.0
        return (cx, cy), (maxx - minx, maxy - miny)
