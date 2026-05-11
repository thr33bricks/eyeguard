import dearpygui.dearpygui as dpg
import cv2
import time
import numpy as np
import mediapipe as mp
import warnings

import settings
import eyes_utils
import eyes_actions
import frame_limiter
import warn

# Suppress MediaPipe protobuf deprecation warnings
warnings.filterwarnings("ignore", category=UserWarning, module="google.protobuf.symbol_database")

def set_fps(sender, app_data, user_data):
    settings.MAX_FPS = app_data
    frame_limiter.frame_time = 1.0 / app_data

def set_calib(sender, app_data, user_data):
    settings.SCREEN_DISTANCE_CALIBRATION = app_data

def main():
    dpg.create_context()
    
    # Initialize camera and read the first frame to get the correct dimensions for DPG texture
    cap = eyes_utils.init_cap()
    success, frame = cap.read()
    if not success:
        print("Failed to read from video source.")
        return
        
    if not settings.USE_WEBCAM:
        frame = eyes_utils.resize_for_video(frame)
        
    h, w, _ = frame.shape
    
    with dpg.texture_registry(show=False):
        default_data = np.zeros((w * h * 4,), dtype=np.float32)
        dpg.add_dynamic_texture(width=w, height=h, default_value=default_data, tag="video_texture")
        
    with dpg.window(tag="Primary Window"):
        with dpg.group(horizontal=True):
            # Video Group
            with dpg.group():
                dpg.add_image("video_texture", tag="video_image")
                
            # Stats & Settings Group
            with dpg.group(width=350):
                dpg.add_text("Dashboard", color=[200, 200, 255])
                dpg.add_separator()
                
                dpg.add_text("FPS: 0.0", tag="fps_text")
                dpg.add_text("Current Screen Dist: 0.0 cm", tag="cur_dist_text")
                dpg.add_text("Squinting: False", tag="cur_squint_text")
                
                dpg.add_spacing(count=2)
                dpg.add_text("Averages", color=[200, 200, 255])
                dpg.add_separator()
                
                dpg.add_text("Avg Blinks/min: 0.0", tag="avg_blinks_text")
                dpg.add_text("Avg Screen Dist: 0.0 cm", tag="avg_dist_text")
                dpg.add_text("Avg Squinting: 0.0", tag="avg_squint_text")
                
                dpg.add_spacing(count=2)
                dpg.add_text("Settings", color=[200, 200, 255])
                dpg.add_separator()
                
                dpg.add_text("FPS Limit")
                dpg.add_slider_int(label="", default_value=settings.MAX_FPS, 
                                   min_value=10, max_value=60, callback=set_fps, width=-1)
                dpg.add_text("Screen Dist Calibration (cm)")
                dpg.add_slider_float(label="", 
                                     default_value=settings.SCREEN_DISTANCE_CALIBRATION, 
                                     min_value=-10.0, max_value=10.0, callback=set_calib, width=-1)

    dpg.create_viewport(title='EyeGuard AI Eye protection - Dashboard', width=1050, height=540)
    dpg.setup_dearpygui()
    dpg.set_global_font_scale(1.2)
    dpg.show_viewport()
    dpg.set_primary_window("Primary Window", True)
    
    settings.SHOW_CAMERA_FEED = False
    warn.init()
    
    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=False,
        min_detection_confidence=0.6,
        min_tracking_confidence=0.6
    )
    
    frame_count = 0
    fps = 0
    
    while dpg.is_dearpygui_running():
        start_time = time.perf_counter()
        
        success, frame = cap.read()
        if not success:
            # Stop processing if video stream ends
            if not settings.USE_WEBCAM:
                break
            continue
            
        if not settings.USE_WEBCAM:
            frame = eyes_utils.resize_for_video(frame)
            
        frame = cv2.flip(frame, 1)
        frame_count += 1
        
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb_frame)
        
        eyes_utils.face = False
        if results.multi_face_landmarks:
            eyes_utils.face = True
            for face_landmarks in results.multi_face_landmarks:
                eyes_utils.update_eye_points(frame, face_landmarks)
                
                if frame_count % settings.CLASSIFY_EVERY_N_FRAMES == 0:
                    if settings.BATCHED_CLASSIFICATION:
                        eyes_utils.show_eyes_batched(frame)
                    else:
                        eyes_utils.show_eye(frame, "left")
                        eyes_utils.show_eye(frame, "right")
                    frame_count = 0
                    
                eyes_utils.calculate_ear()
                eyes_utils.draw_ui_main_frame(frame)
                
        eyes_actions.update()
        warn.update()
        
        # Update DearPyGui Video Texture Data
        rgba_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
        texture_data = rgba_frame.ravel().astype(np.float32) / 255.0
        dpg.set_value("video_texture", texture_data)
        
        # Update UI texts metrics
        dpg.set_value("fps_text", f"FPS: {fps:.1f}")
        dpg.set_value("cur_dist_text", f"Current Screen Dist: {eyes_actions.screen_distance:.1f} cm")
        dpg.set_value("cur_squint_text", f"Squinting: {eyes_actions.squinting}")
        
        dpg.set_value("avg_blinks_text", f"Avg Blinks/min: {warn.avg_blinks_pm:.1f}")
        dpg.set_value("avg_dist_text", f"Avg Screen Dist: {warn.avg_screen_distance:.1f} cm")
        dpg.set_value("avg_squint_text", f"Avg Squinting: {warn.avg_squinting:.1f}")

        # Scale video feed dynamically on window resize
        vp_w = dpg.get_viewport_client_width()
        vp_h = dpg.get_viewport_client_height()
        
        if vp_w > 400 and vp_h > 50:
            avail_w = vp_w - 380  # Account for settings panel + horizontal padding
            avail_h = vp_h - 40   # Account for vertical padding
            
            target_w = avail_w
            target_h = int(target_w * (h / w))
            
            if target_h > avail_h:
                target_h = avail_h
                target_w = int(target_h * (w / h))
                
            dpg.configure_item("video_image", width=target_w, height=target_h)

        # End frame tracking and Limit FPS dynamically
        end_time = time.perf_counter()
        frame_limiter.limit(end_time - start_time)
        
        total_frame_time = time.perf_counter() - start_time
        fps = 1.0 / total_frame_time if total_frame_time > 0 else 0.0
        
        dpg.render_dearpygui_frame()

    cap.release()
    face_mesh.close()
    dpg.destroy_context()

if __name__ == "__main__":
    main()
