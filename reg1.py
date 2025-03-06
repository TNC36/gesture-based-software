import cv2
import pickle
import os
from insightface.app import FaceAnalysis
from main import register_User_file as r
# Create database folder if it doesn't exist
db_folder = "database"
os.makedirs(db_folder, exist_ok=True)

# Initialize face recognition model
face_analysis = FaceAnalysis()
face_analysis.prepare(ctx_id=0, det_size=(640, 640))

# Open the camera
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

print("Capturing reference face. Please align your face in the frame...")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Error: Could not read frame.")
        break
    
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    faces = face_analysis.get(frame_rgb)
    
    if faces:
        reference_face_encoding = faces[0].embedding
        names=r()
        print(names)
        file_path = os.path.join(db_folder, f"{names}.pkl")
        with open(file_path, "wb") as f:
            pickle.dump(reference_face_encoding, f)
        
        print(f"Reference face saved successfully in {file_path}.")
        break
    
    cv2.imshow("Capture Reference Face", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
