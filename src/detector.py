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

        style = mp.solutions.drawing_utils.DrawingSpec(
            color=(0, 255, 0),
            thickness=1,
            circle_radius=1
        )

        for face_landmarks in results.multi_face_landmarks:
            mp.solutions.drawing_utils.draw_landmarks(
                image=frame,
                landmark_list=face_landmarks,
                connections=mp.solutions.face_mesh.FACEMESH_LEFT_EYE,
                landmark_drawing_spec=None,
                connection_drawing_spec=style
            )

            mp.solutions.drawing_utils.draw_landmarks(
                image=frame,
                landmark_list=face_landmarks,
                connections=mp.solutions.face_mesh.FACEMESH_RIGHT_EYE,
                landmark_drawing_spec=None,
                connection_drawing_spec=style
            )

    def face_center_and_bbox(self, landmarks, w, h):
        xs = [landmarks[i].x * w for i in range(len(landmarks))]
        ys = [landmarks[i].y * h for i in range(len(landmarks))]
        minx, maxx = min(xs), max(xs)
        miny, maxy = min(ys), max(ys)
        cx = (minx + maxx) / 2.0
        cy = (miny + maxy) / 2.0
        return (cx, cy), (maxx - minx, maxy - miny)

    def is_looking_at_camera(self, landmarks):
        # 1 - czubek nosa
        # 33, 263 - lewa, prawa skroń
        # 10 - górna krawędź czoła (pion)
        # 152 - dolna krawędź brody (pion)

        # Distance from nose to left and right side of face (in X axis)
        nose = landmarks[1]
        left_side = landmarks[33]
        right_side = landmarks[263]
        dist_left = abs(nose.x - left_side.x)
        dist_right = abs(nose.x - right_side.x)

        # Calc ratio horizontal - ideally close to 1
        ratio_h = dist_left / dist_right if dist_right != 0 else 0

        # Y axis - distance from nose to top and bottom of face
        top_side = landmarks[10]
        bottom_side = landmarks[152]
        dist_top = abs(nose.y - top_side.y)
        dist_bottom = abs(nose.y - bottom_side.y)

        ratio_v = dist_top / dist_bottom if dist_bottom != 0 else 0

        # Check if ratios are within tolerance
        h_lower = 1.0 - config.LOOK_TOLERANCE
        h_upper = 1.0 + config.LOOK_TOLERANCE
        v_lower = 0.8
        v_upper = 2.0

        horizontal_ok = h_lower < ratio_h < h_upper
        vertical_ok = v_lower < ratio_v < v_upper

        return horizontal_ok and vertical_ok