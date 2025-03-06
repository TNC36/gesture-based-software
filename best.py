import sys
import os
import cv2
import pickle
import numpy as np
from scipy.spatial.distance import cosine
from insightface.app import FaceAnalysis
import mediapipe as mp
import pyautogui
import pyttsx3
import time
import pydirectinput as p
from PyQt6.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import QTimer
from pynput.keyboard import Controller

class GestureApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gesture & Eye Tracking App")
        self.setGeometry(100, 100, 800, 600)

        # UI Elements
        self.label = QLabel("Click 'Start' to begin", self)
        self.start_btn = QPushButton("Start Camera", self)
        self.stop_btn = QPushButton("Stop Camera", self)
        self.image_label = QLabel(self)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.image_label)
        layout.addWidget(self.start_btn)
        layout.addWidget(self.stop_btn)
        self.setLayout(layout)

        # Buttons
        self.start_btn.clicked.connect(self.auth_face)
        self.stop_btn.clicked.connect(self.stop_camera)

        # Camera & Timer
        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

        # Mediapipe for hand & face tracking
        # self.hands = mp.solutions.hands.Hands()
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands()
        self.face_mesh = mp.solutions.face_mesh.FaceMesh(refine_landmarks=True)
        self.mp_draw = mp.solutions.drawing_utils

        # Keyboard Controller
        self.keyboard = Controller()
        self.screen_w, self.screen_h = pyautogui.size()

        # Face Recognition Setup
        self.face_rec = FaceAnalysis()
        self.face_rec.prepare(ctx_id=0, det_size=(640, 640))
        self.known_faces = self.load_faces()

    def load_faces(self):
        """Load stored face encodings from database."""
        faces = {}
        db_path = "database/"
        os.makedirs(db_path, exist_ok=True)

        for file in os.listdir(db_path):
            if file.endswith(".pkl"):
                with open(os.path.join(db_path, file), "rb") as f:
                    faces[file.replace(".pkl", "")] = pickle.load(f)
        return faces

    def auth_face(self):
        """Authenticate user via face recognition before starting tracking."""
        if not self.known_faces:
            self.label.setText("No registered faces. Please add one first.")
            return

        self.cap = cv2.VideoCapture(0)
        # self.cap = cv2.VideoCapture(1)
        self.label.setText("Align your face for authentication...")

        access = False
        for _ in range(50):  # Try to detect face for 50 frames
            ret, frame = self.cap.read()
            if not ret:
                continue

            faces = self.face_rec.get(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            if faces:
                detected = faces[0].embedding
                for user, stored in self.known_faces.items():
                    similarity = 1 - cosine(detected, stored)
                    if similarity > 0.5:
                        access = True
                        break
            
            cv2.imshow("Face Authentication", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.cap.release()
        cv2.destroyAllWindows()

        if access:
            self.label.setText("Access Granted. Starting tracking...")
            self.start_camera()
        else:
            self.label.setText("Access Denied. Try again.")

    def start_camera(self):
        """Start video feed for gesture and eye tracking."""
        self.cap = cv2.VideoCapture(0)
        self.timer.start(30)

    def stop_camera(self):
        """Stop camera feed."""
        self.timer.stop()
        if self.cap:
            self.cap.release()
        self.image_label.clear()

    def update_frame(self):
        """Process the video frame for hand gestures and eye tracking."""
        ret, frame = self.cap.read()
        if not ret:
            return

        frame = cv2.flip(frame, 1)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        hand_results = self.hands.process(frame_rgb)
        face_results = self.face_mesh.process(frame_rgb)

        engine = pyttsx3.init()
        action = "No Hand Detected"

        # Hand tracking logic
        if hand_results.multi_hand_landmarks:
            for hand_landmarks in hand_results.multi_hand_landmarks:
                fingers = self.detect_fingers(hand_landmarks)

                # Simple if-else conditions for gesture actions
                if fingers == [1, 1, 1, 1, 1]:
                    action = "Move Forward"
                    p.keyDown('w')
                elif fingers == [0, 0, 0, 0, 0]:
                    action = "Stop"
                    p.keyDown('s')
                elif fingers == [1, 0, 0, 0, 0]:
                    action = "Move Right"
                    p.keyDown('d')
                elif fingers == [1, 1, 0, 0, 0]:
                    action = "Move Left"
                    p.keyDown('a')
                elif fingers == [0, 1, 1, 0, 0]:
                    action = "Click"
                    pyautogui.click()
                    # time.sleep(1)

                # engine.say(action)
                # engine.runAndWait()
                self.mp_draw.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)

        # Eye tracking logic
        if face_results.multi_face_landmarks:
            landmarks = face_results.multi_face_landmarks[0].landmark
            right_eye = landmarks[474]
            cursor_x = right_eye.x * self.screen_w
            cursor_y = right_eye.y * self.screen_h
            pyautogui.moveTo(cursor_x, cursor_y)

        # Show detected action on screen
        cv2.putText(frame_rgb, action, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (121, 5, 76), 2, cv2.LINE_AA)
        h, w, ch = frame_rgb.shape
        qimg = QImage(frame_rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
        self.image_label.setPixmap(QPixmap.fromImage(qimg))

    def detect_fingers(self, hand_landmarks):
        """
        Detect which fingers are up based on hand landmarks.
        Returns a list of 5 values: [thumb, index, middle, ring, pinky]
        """
        fingers = []
        tips = [4, 8, 12, 16, 20]  # Landmark indices for fingertips
        pips = [2, 6, 10, 14, 18]  # Landmark indices for PIP joints (lower joint in the finger)

        # Check thumb separately (thumb moves sideways)
        if hand_landmarks.landmark[4].x < hand_landmarks.landmark[3].x:  # Right hand
            fingers.append(1)  # Thumb is extended
        elif hand_landmarks.landmark[4].x > hand_landmarks.landmark[3].x:  # Left hand
            fingers.append(0)  # Thumb is folded
        else:
            fingers.append(-2)  # Thumb is folded

        # Check remaining fingers (index, middle, ring, pinky)
        for tip, pip in zip(tips[1:], pips[1:]):  # Skip thumb
            if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[pip].y:
                fingers.append(1)  # Finger is up
            else:
                fingers.append(0)  # Finger is down

        return fingers  # Example output: [1, 1, 0, 0, 0] (Thumb and Index Up)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GestureApp()
    window.show()
    sys.exit(app.exec())
