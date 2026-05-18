import os
import sys
import cv2
import time
import settings
from fastai.vision.all import *
import timm

import torch
import torchvision.transforms as T
transform = T.Compose([
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225])
])

if torch.cuda.is_available():
    DEVICE = torch.device('cuda')
    USE_HALF = True
else:
    DEVICE = torch.device('cpu')
    USE_HALF = False

print(f"Internal Path (sys._MEIPASS): {getattr(sys, '_MEIPASS', 'Not in EXE')}")
def get_model_path(relative_path):
    """ Get the absolute path to the model file """
    if hasattr(sys, '_MEIPASS'):
        # This is where PyInstaller unzips files
        return os.path.join(sys._MEIPASS, relative_path)
    # This is where the file is during development
    return os.path.abspath(relative_path)

model_path = get_model_path('Dev/models/' + settings.EYE_MODEL_NAME)
LEARNER = load_learner(model_path)
LEARNER.model.eval()
LEARNER.model.to(DEVICE)
if USE_HALF:
    LEARNER.model.half()

# Precomputed normalization tensors directly on the selected device
mean_tensor = torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1).to(DEVICE)
std_tensor = torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1).to(DEVICE)
if USE_HALF:
    mean_tensor = mean_tensor.half()
    std_tensor = std_tensor.half()

# Landmark indices for MediaPipe Face Mesh
RIGHT_EYE = [362, 385, 387, 263, 373, 380]
LEFT_EYE = [33, 160, 158, 133, 153, 144]

right_eye_pts = []
left_eye_pts = []
landmark_coords = []

# EAR values
left_ear = 0.0
right_ear = 0.0
avg_ear = 0.0
min_ear = 0.0

# Eye states
left_eye_state = "unknown"
right_eye_state = "unknown"
left_eye_new_state = False
right_eye_new_state = False

#
face = False

def print_verbose(*args):
    if settings.PRINT_VERBOSE:
        print(*args)

# Just a pythagorean
def euclidean(p1, p2):
    return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

def get_vertical_distance(eye_points):
    return (euclidean(eye_points[1], eye_points[5]) + euclidean(eye_points[2], eye_points[4])) / 2.0

def ear(eye_points):
    # Horizontal
    h = euclidean(eye_points[0], eye_points[3])
    return (get_vertical_distance(eye_points)) / h

def calculate_ear():
    global left_ear, right_ear, avg_ear, min_ear
    left_ear = ear(left_eye_pts)
    right_ear = ear(right_eye_pts)

    avg_ear = (left_ear + right_ear) / 2.0
    min_ear = min(left_ear, right_ear)

def show_face(frame):
    if not settings.SHOW_CAMERA_FEED:
        return None
    
    # Face bounding box
    x_coords = [p[0] for p in landmark_coords]
    y_coords = [p[1] for p in landmark_coords]
    min_x, max_x = min(x_coords), max(x_coords)
    min_y, max_y = min(y_coords), max(y_coords)
    #cv2.rectangle(frame, (min_x, min_y), (max_x, max_y), (255, 255, 0), 2)
    
    face_crop = frame[min_y:max_y, min_x:max_x]
    if face_crop.size > 0:
        ratio = settings.FACE_HEIGHT / face_crop.shape[0]
        face_crop = cv2.resize(face_crop, None, fx=ratio, fy=ratio)
        cv2.imshow('Face', face_crop)

        return face_crop
    return None

def crop_eye(frame, eye, height_ratio=1.0):
    NATURAL_TILT_COMPENSATION = 0.1
    if eye == "left":
        NATURAL_TILT_COMPENSATION *= -1
        string = "Left Eye"
        eye_points = left_eye_pts
    elif eye == "right":
        string = "Right Eye"
        eye_points = right_eye_pts

    left = eye_points[0]  # Left corner
    right = eye_points[3]  # Right corner

    dx = right[0] - left[0]
    dy = right[1] - left[1]
    width = np.sqrt(dx**2 + dy**2)
    angle = np.degrees(np.arctan2(dy, dx) + NATURAL_TILT_COMPENSATION)
    
    # Center
    center = ((left[0] + right[0]) / 2, (left[1] + right[1]) / 2)
    
    # Rotation matrix
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    
    # Calculate dimentsions
    h = int(width * height_ratio * settings.EYE_CROP_ASPECT_RATIO)
    w = int(width * settings.EYE_CROP_ASPECT_RATIO)

    # Update translation parts of the matrix to move 'center' to (w/2, h/2)
    M[0, 2] += (w / 2) - center[0]
    M[1, 2] += (h / 2) - center[1]
    
    # Rotate the image
    eye_crop = cv2.warpAffine(frame, M, (w, h))
    eye_crop = cv2.resize(eye_crop, (128, 128), interpolation=cv2.INTER_AREA)

    return string, eye_crop

def crop_and_classify(frame, eye, height_ratio=1.0):
    string, eye_crop = crop_eye(frame, eye, height_ratio)

    if eye_crop.size > 0:
        start_time = time.perf_counter()
        #label, conf = classify_eye(eye_crop)
        label, conf = classify_eye_fast(eye_crop)
        end_time = time.perf_counter()
        latency = end_time - start_time

        if settings.PRINT_CLASSIFIER_RESULTS:
            print_verbose(f"Time: {latency:.4f}s | Eye: {eye} | Label: {label} | Conf: {conf:.2%}")

        global left_eye_state, right_eye_state, left_eye_new_state, right_eye_new_state
        if eye == "left":
            left_eye_new_state = True
            left_eye_state = label
        elif eye == "right":
            right_eye_new_state = True
            right_eye_state = label

        return string, eye_crop, label, conf
    
def crop_and_classify_batched(frame):
    left_string, left_crop = crop_eye(frame, "left")
    right_string, right_crop = crop_eye(frame, "right")

    if left_crop.size > 0 and right_crop.size > 0:
        start_time = time.perf_counter()
        results = classify_eyes_batched(left_crop, right_crop)
        end_time = time.perf_counter()
        latency = end_time - start_time

        global left_eye_state, right_eye_state, left_eye_new_state, right_eye_new_state
        left_eye_new_state = True
        right_eye_new_state = True
        left_eye_state = results[0][0]
        right_eye_state = results[1][0]

        if settings.PRINT_CLASSIFIER_RESULTS:
            print_verbose(f"Time: {latency:.4f}s | Left Eye: {results[0][0]} ({results[0][1]:.2%}) | Right Eye: {results[1][0]} ({results[1][1]:.2%})")

        return (left_string, left_crop, results[0][0], results[0][1]), (right_string, right_crop, results[1][0], results[1][1])

def show_eyes_batched(frame):
    left_result, right_result = crop_and_classify_batched(frame)
    if left_result and right_result:
        show_eye_no_classify(left_result[0], left_result[1], left_result[2])
        show_eye_no_classify(right_result[0], right_result[1], right_result[2])

def show_eye_no_classify(string, eye_crop, label):
    # Open - green, Closed - red, Unknown - magenta, Uncertain - yellow
    if not settings.SHOW_CAMERA_FEED:
        return
    
    if label == "open":
        color = (0, 255, 0) 
    elif label == "closed":
        color = (0, 0, 255) 
    elif label == "unknown":
        color = (255, 0, 255)
    elif label == "uncertain": 
        color = (0, 255, 255)

    cv2.putText(eye_crop, label, (0, 12), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 1)
    cv2.imshow(string, eye_crop)

def show_eye(frame, eye):
    string, eye_crop, label, conf = crop_and_classify(frame, eye)

    if not settings.SHOW_CAMERA_FEED:
        return

    # Open - green, Closed - red, Unknown - magenta, Uncertain - yellow
    if label == "open":
        color = (0, 255, 0) 
    elif label == "closed":
        color = (0, 0, 255) 
    elif label == "unknown":
        color = (255, 0, 255)
    elif label == "uncertain": 
        color = (0, 255, 255)

    eye_crop_no_text = eye_crop.copy()
    cv2.putText(eye_crop, label, (0, 12), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 1)
    cv2.imshow(string, eye_crop)

    # Save left or right eye
    # key = cv2.waitKey(1) & 0xFF
    # #if key == ord('s') and eye == "right":  # press 's' to save
    # if key == ord('s') and eye == "left":  # press 's' to save
    #     save_dir = "photos_eyes"
    #     os.makedirs(save_dir, exist_ok=True)

    #     filename = f"{eye}_{int(time.time())}.jpg"
    #     filepath = os.path.join(save_dir, filename)

    #     cv2.resize(frame, (90, 90), interpolation=cv2.INTER_AREA)
    #     cv2.imwrite(filepath, eye_crop_no_text)
    #     print(f"Saved: {filepath}")

def classify_eye(eye_np_array):
    img_rgb = cv2.cvtColor(eye_np_array, cv2.COLOR_BGR2RGB)
    img = PILImage.create(img_rgb)
    
    # Predict
    pred, pred_idx, probs = LEARNER.predict(img)
    confidence = probs[pred_idx].item()
    
    if confidence < settings.EYE_MODEL_UNCERT_THRES:
        return "uncertain", confidence
    return pred, confidence

def classify_eye_fast(eye_np_array):
    img = cv2.cvtColor(eye_np_array, cv2.COLOR_BGR2RGB)

    # Fast Preprocessing
    tensor = torch.from_numpy(img).permute(2, 0, 1).unsqueeze(0).to(DEVICE)
    if USE_HALF:
        tensor = tensor.half()
    tensor = tensor / 255.0
    tensor = (tensor - mean_tensor) / std_tensor

    with torch.no_grad():
        outputs = LEARNER.model(tensor)
        probs = torch.softmax(outputs, dim=1)
        conf, pred_idx = torch.max(probs, dim=1)

    label = LEARNER.dls.vocab[pred_idx.item()]
    confidence = conf.item()

    if confidence < settings.EYE_MODEL_UNCERT_THRES:
        return "uncertain", confidence

    return label, confidence

import torch
import cv2

def classify_eyes_batched(left_eye_np, right_eye_np):
    # 1. Preprocess both images
    img_l = cv2.cvtColor(left_eye_np, cv2.COLOR_BGR2RGB)
    img_r = cv2.cvtColor(right_eye_np, cv2.COLOR_BGR2RGB)

    # 2. Fast Batch Preprocessing
    batch_np = np.stack([img_l, img_r])
    batch_tensor = torch.from_numpy(batch_np).permute(0, 3, 1, 2).to(DEVICE)
    if USE_HALF:
        batch_tensor = batch_tensor.half()
    batch_tensor = batch_tensor / 255.0
    
    # Normalize directly on Device
    batch_tensor = (batch_tensor - mean_tensor) / std_tensor

    results = []

    with torch.no_grad():
        # 3. Single pass through the model
        outputs = LEARNER.model(batch_tensor)
        
        # 4. Process the batch results
        probs = torch.softmax(outputs, dim=1)
        confidences, pred_idxs = torch.max(probs, dim=1)

    # 5. Extract labels and handle uncertainty for both
    for i in range(2):
        conf = confidences[i].item()
        idx = pred_idxs[i].item()
        label = LEARNER.dls.vocab[idx]

        if conf < settings.EYE_MODEL_UNCERT_THRES:
            results.append(("uncertain", conf))
        else:
            results.append((label, conf))

    return results  # Returns [(left_label, left_conf), (right_label, right_conf)]

def init_cap():
    cap = cv2.VideoCapture(0) if settings.USE_WEBCAM else cv2.VideoCapture(settings.VIDEO_PATH)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, settings.CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, settings.CAMERA_HEIGHT)
    return cap

def draw_ui_main_frame(frame):
    # Draw eye landmarks for visual tracking
    for (x, y) in left_eye_pts + right_eye_pts:
        cv2.circle(frame, (x, y), 2, (0, 255, 255), -1)

    # UI Color logic
    status = "CLOSED" if min_ear < settings.EAR_THRESHOLD else "OPEN"
    color = (0, 0, 255) if status == "CLOSED" else (0, 255, 0)
    
    # Display min EAR value
    cv2.putText(frame, f"Min EAR:   {min_ear:.2f}", (30, 40), 
                cv2.FONT_HERSHEY_DUPLEX, 0.7, color, 2)
    
    # Big status text
    cv2.putText(frame, status, (30, 80), 
                cv2.FONT_HERSHEY_DUPLEX, 1.5, color, 2)
    
def update_eye_points(frame, face_landmarks):
    h, w, _ = frame.shape

    global landmark_coords, right_eye_pts, left_eye_pts
    #landmark_coords = [(int(p.x * w), int(p.y * h)) for p in face_landmarks.landmark]
    right_eye_pts = [(int(face_landmarks.landmark[i].x * w), 
                      int(face_landmarks.landmark[i].y * h)) for i in RIGHT_EYE]
    left_eye_pts = [(int(face_landmarks.landmark[i].x * w), 
                     int(face_landmarks.landmark[i].y * h)) for i in LEFT_EYE]

def resize_for_video(frame):
    h, w = frame.shape[:2]
    ratio = settings.VIDEO_WIDTH / float(w)
    return cv2.resize(frame, (settings.VIDEO_WIDTH, int(h * ratio)), interpolation=cv2.INTER_AREA)
