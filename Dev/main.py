# EAR and open/closed/occluded classifier using mediapipe face mesh and a custom eye model trained using fastai
# Yordan Yordanov, April 2026

import cv2
import time
import mediapipe as mp
import settings
import eyes_utils
import eyes_actions
import frame_limiter
import warn


frame_count = 0

mp_face_mesh = mp.solutions.face_mesh
cap = eyes_utils.init_cap()

# Initialize MediaPipe Face Mesh
with mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=False,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6) as face_mesh:

    while cap.isOpened():
        start_time = time.perf_counter()
        success, frame = cap.read()
        if not success: break
        if not settings.USE_WEBCAM:
            frame = eyes_utils.resize_for_video(frame)

        frame = cv2.flip(frame, 1)  # Mirror frame
        frame_count += 1

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb_frame)

        eyes_utils.face = False
        if results.multi_face_landmarks:
            eyes_utils.face = True

            for face_landmarks in results.multi_face_landmarks:
                eyes_utils.update_eye_points(frame, face_landmarks)

                if frame_count % settings.CLASSIFY_EVERY_N_FRAMES == 0:
                    # Draw both eyes with classifier results
                    if settings.BATCHED_CLASSIFICATION:
                        eyes_utils.show_eyes_batched(frame)
                    else:
                        eyes_utils.show_eye(frame, "left")
                        eyes_utils.show_eye(frame, "right")
                    frame_count = settings.CLASSIFY_EVERY_N_FRAMES

                # Calculate EAR
                eyes_utils.calculate_ear()

                # Draw EAR values and eye status based on EAR threshold
                eyes_utils.draw_ui_main_frame(frame)

        if settings.SHOW_CAMERA_FEED:
            cv2.imshow(settings.MAIN_WINDOW_TITLE, frame)
            if cv2.waitKey(1) & 0xFF == 27: break # ESC
        end_time = time.perf_counter()

        frame_limiter.limit(end_time - start_time)
        total_frame_time = time.perf_counter() - start_time

        if settings.PRINT_FRAME_TIME:
            eyes_utils.print_verbose(f"Frame time: {total_frame_time:.4f}s | FPS: {1 / total_frame_time:.2f}")

        eyes_actions.update()
        warn.update()

cap.release()
cv2.destroyAllWindows()
