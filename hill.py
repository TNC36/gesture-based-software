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
from pynput.keyboard import Controller, Key

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
        self.start_btn.clicked.connect(self.authenticate_and_start)
        self.stop_btn.clicked.connect(self.stop_camera)

        # Camera & Timer
        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

        # Hand & Face Mesh
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands()
        self.mp_draw = mp.solutions.drawing_utils
        self.face_mesh = mp.solutions.face_mesh.FaceMesh(refine_landmarks=True)

        # Keyboard Controller
        self.keyboard_controller = Controller()
        self.screen_w, self.screen_h = pyautogui.size()

        # Face Recognition Setup
        self.face_analysis = FaceAnalysis()
        self.face_analysis.prepare(ctx_id=0, det_size=(640, 640))
        self.known_faces = self.load_known_faces()

    def load_known_faces(self):
        """Load all stored face encodings from the database folder."""
        known_faces = {}
        database_path = "database/"
        if not os.path.exists(database_path):
            os.makedirs(database_path)
        
        for file in os.listdir(database_path):
            if file.endswith(".pkl"):
                user_name = file.replace(".pkl", "")
                with open(os.path.join(database_path, file), "rb") as f:
                    known_faces[user_name] = pickle.load(f)
        return known_faces

    def authenticate_and_start(self):
        if not self.known_faces:
            self.label.setText("No registered face found. Please register first.")
            return

        self.cap = cv2.VideoCapture(0)
        self.label.setText("Authenticating... Align your face.")
        access_granted = False

        for _ in range(100):
            ret, frame = self.cap.read()
            if not ret:
                continue
            
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            faces = self.face_analysis.get(frame_rgb)
            
            if faces:
                detected_encoding = faces[0].embedding
                for user_name, stored_encoding in self.known_faces.items():
                    similarity = 1 - cosine(detected_encoding, stored_encoding)
                    if similarity > 0.5:
                        access_granted = True
                        break
            
            cv2.imshow("Face Authentication", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.cap.release()
        cv2.destroyAllWindows()

        if access_granted:
            self.label.setText("Access Granted. Starting Gesture & Eye Tracking...")
            self.start_camera()
        else:
            self.label.setText("Access Denied. Try Again.")

    def start_camera(self):
        self.cap = cv2.VideoCapture(0)
        self.timer.start(30)

    def stop_camera(self):
        self.timer.stop()
        if self.cap:
            self.cap.release()
        self.image_label.clear()

    def update_frame(self):
        keyboard_controller=Controller()
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.flip(frame, 1)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            hand_results = self.hands.process(frame_rgb)
            face_results = self.face_mesh.process(frame_rgb)

            engine = pyttsx3.init()
            gesture = "No Hand Detected"
            if hand_results.multi_hand_landmarks:
                for hand_landmarks in hand_results.multi_hand_landmarks:
                    fingers = self.fingers_up(hand_landmarks)
                    if fingers == [1,1, 1, 1, 1]:
                        gesture = "forward"
                        keyboard_controller.release(Key.left)
                        keyboard_controller.press(Key.right)
                        
                    elif fingers == [0, 0, 0, 0, 0]:
                        gesture = "brake"
                        keyboard_controller.release(Key.right)
                        keyboard_controller.press(Key.left)
                        
                    elif fingers == [0, 1, 1, 0, 0]:
                        gesture = "Click"
                        pyautogui.click()
                        pyautogui.sleep(1)
                    engine.say(gesture)
                    engine.runAndWait()
                    self.mp_draw.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)

            if face_results.multi_face_landmarks:
                landmarks = face_results.multi_face_landmarks[0].landmark
                right_eye = landmarks[474]
                cursor_x = right_eye.x * self.screen_w
                cursor_y = right_eye.y * self.screen_h
                pyautogui.moveTo(cursor_x, cursor_y)

            cv2.putText(frame_rgb, gesture, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (121, 5, 76), 2, cv2.LINE_AA)
            h, w, ch = frame_rgb.shape
            qimg = QImage(frame_rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
            self.image_label.setPixmap(QPixmap.fromImage(qimg))

    def fingers_up(self, hand_landmarks):
        fingers = []
        tips = [4, 8, 12, 16, 20]
        pips = [2, 6, 10, 14, 18]

        if hand_landmarks.landmark[4].x < hand_landmarks.landmark[3].x:
            fingers.append(1)
        else:
            fingers.append(0)

        for tip, pip in zip(tips[1:], pips[1:]):
            fingers.append(1 if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[pip].y else 0)

        return fingers

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GestureApp()
    window.show()
    sys.exit(app.exec())
