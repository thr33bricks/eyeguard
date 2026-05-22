import os
import sys
import ctypes

# --- FORCE MEDIAPIPE'S BACKEND THREADS TO SLEEP INSTEAD OF SPINNING ---
if sys.platform == "win32":
    os.environ["OMP_WAIT_POLICY"] = "PASSIVE"
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"

import dearpygui.dearpygui as dpg
import cv2
import time
import numpy as np
import mediapipe as mp  # 0.10.14
import warnings
import json
import threading

import startup
import settings
import eyes_utils
import eyes_actions
import frame_limiter
import warn

# System tray dependencies
import pystray
from PIL import Image

# Suppress MediaPipe protobuf deprecation warnings
warnings.filterwarnings("ignore", category=UserWarning, module="google.protobuf.symbol_database")

def get_base_dir():
    if hasattr(sys, 'frozen'):
        if hasattr(sys, '_MEIPASS'):
            return sys._MEIPASS
        return os.path.dirname(os.path.abspath(sys.executable))
    
    return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = get_base_dir()
SETTINGS_FILE = os.path.join(BASE_DIR, "user_settings.json")

# Global lifecycle flag for our background thread
app_running = True
tray_icon = None

# --- WINDOW MANAGER HELPER ---
class WindowManager:
    def __init__(self, title):
        self.title = title

    def hide(self, icon=None, item=None):
        if sys.platform == "win32":
            hwnd = ctypes.windll.user32.FindWindowW(None, self.title)
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 0)  # 0 = SW_HIDE

    def show(self, icon=None, item=None):
        if sys.platform == "win32":
            hwnd = ctypes.windll.user32.FindWindowW(None, self.title)
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 9)  # 9 = SW_RESTORE (restores from minimized)

window = WindowManager("EyeGuard AI Eye protection - Dashboard")

def load_user_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
                if "MAX_FPS" in data:
                    settings.MAX_FPS = data["MAX_FPS"]
                if "SCREEN_DISTANCE_CALIBRATION" in data:
                    settings.SCREEN_DISTANCE_CALIBRATION = data["SCREEN_DISTANCE_CALIBRATION"]
        except Exception:
            pass

def save_user_settings():
    data = {
        "MAX_FPS": settings.MAX_FPS,
        "SCREEN_DISTANCE_CALIBRATION": settings.SCREEN_DISTANCE_CALIBRATION
    }
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception:
        pass

def set_fps(sender, app_data, user_data):
    settings.MAX_FPS = app_data
    save_user_settings()

def set_calib(sender, app_data, user_data):
    settings.SCREEN_DISTANCE_CALIBRATION = app_data
    save_user_settings()

def toggle_autostart(sender, app_data, user_data):
    if app_data:
        startup.enable_autostart()
    else:
        startup.disable_autostart()

def quit_window(icon, item):
    global app_running
    app_running = False
    if icon:
        icon.stop()
    if dpg.is_dearpygui_running():
        dpg.stop_dearpygui()

def camera_worker_thread(cap, h, w):
    global app_running
    
    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=False,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )

    frame_count = 0
    fps = 0
    frame_skip_counter = 0
    process_every_n_frames = 2

    while app_running:
        start_time = time.perf_counter()
        
        success, frame = cap.read()
        if not success:
            if not settings.USE_WEBCAM:
                break
            time.sleep(0.033)
            continue
            
        if not settings.USE_WEBCAM:
            frame = eyes_utils.resize_for_video(frame)
            
        frame = cv2.flip(frame, 1)
        frame_count += 1
        frame_skip_counter += 1
        
        # 1. Process face mesh at the specified interval
        if frame_skip_counter % process_every_n_frames == 0:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(rgb_frame)
            frame_skip_counter = 0
            
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
                    eyes_utils.draw_ui_main_frame(frame) # Draws UI overlays on the face
            else:
                eyes_utils.face = False
        else:
            # If skipping processing this frame, maintain the overlay if a face was last seen
            if eyes_utils.face:
                eyes_utils.draw_ui_main_frame(frame)
        
        # 2. Update status and warning states
        eyes_actions.update()
        warn.update()
        
        # 3. CRITICAL FIX: Convert and push the texture EVERY frame
        # This keeps the video stream buttery smooth even when no face is present
        rgba_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
        texture_data = rgba_frame.ravel().astype(np.float32) / 255.0
        
        if dpg.is_dearpygui_running() and dpg.is_viewport_ok():
            dpg.set_value("video_texture", texture_data)
            dpg.set_value("fps_text", f"FPS: {fps:.1f}")
            dpg.set_value("cur_dist_text", f"Current Screen Dist: {eyes_actions.screen_distance:.1f} cm")
            dpg.set_value("cur_squint_text", f"Squinting: {eyes_actions.squinting}")
            dpg.set_value("avg_blinks_text", f"Avg Blinks/min: {warn.avg_blinks_pm:.1f}")
            dpg.set_value("avg_dist_text", f"Avg Screen Dist: {warn.avg_screen_distance:.1f} cm")
            dpg.set_value("avg_squint_text", f"Avg Squinting: {warn.avg_squinting:.1f}")

            vp_w = dpg.get_viewport_client_width()
            vp_h = dpg.get_viewport_client_height()
            if vp_w > 400 and vp_h > 50:
                avail_w = vp_w - 380
                avail_h = vp_h - 40
                target_w = avail_w
                target_h = int(target_w * (h / w))
                if target_h > avail_h:
                    target_h = avail_h
                    target_w = int(target_h * (w / h))
                dpg.configure_item("video_image", width=target_w, height=target_h)

        elapsed = time.perf_counter() - start_time
        target_frame_time = 1.0 / settings.MAX_FPS
        if elapsed < target_frame_time:
            time.sleep(target_frame_time - elapsed)
            
        total_time = time.perf_counter() - start_time
        fps = 1.0 / total_time if total_time > 0 else 0.0

    cap.release()
    face_mesh.close()

def main():
    global app_running, tray_icon
    
    if sys.platform == "win32":
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("EyeGuard.AIProtection.1.2-Threaded")
        except Exception:
            pass
    
    load_user_settings()
    startup.install_linux_desktop_file(BASE_DIR)
    
    dpg.create_context()

    cap = eyes_utils.init_cap()
    success, frame = cap.read()
    if not success:
        return

    if not settings.USE_WEBCAM:
        frame = eyes_utils.resize_for_video(frame)

    h, w, _ = frame.shape

    with dpg.texture_registry(show=False):
        default_data = np.zeros((w * h * 4,), dtype=np.float32)
        dpg.add_dynamic_texture(width=w, height=h, default_value=default_data, tag="video_texture")

    with dpg.window(tag="Primary Window"):
        with dpg.group(horizontal=True):
            with dpg.group():
                dpg.add_image("video_texture", tag="video_image")
                
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
                                     min_value=-30.0, max_value=30.0, callback=set_calib, width=-1)
                
                dpg.add_checkbox(
                    label="Launch on startup",
                    default_value=startup.is_autostart_enabled(),
                    callback=toggle_autostart
                )
                
                dpg.add_spacing(count=2)
                dpg.add_button(label="Hide to Tray", callback=lambda: window.hide(), width=-1)

    dpg.create_viewport(title='EyeGuard AI Eye protection - Dashboard', width=1050, height=540, vsync=True)
    
    # Initialize Tray Icon
    icon_path = os.path.join(BASE_DIR, "eyeguard_icon.ico")
    if os.path.exists(icon_path):
        try:
            dpg.set_viewport_small_icon(icon_path)
            dpg.set_viewport_large_icon(icon_path)
            icon_image = Image.open(icon_path)
        except Exception:
            icon_image = Image.new('RGB', (64, 64), color=(30, 30, 30))
    else:
        icon_image = Image.new('RGB', (64, 64), color=(30, 30, 30))

    tray_menu = pystray.Menu(
        pystray.MenuItem("Show", window.show, default=True),
        pystray.MenuItem("Hide", window.hide),
        pystray.MenuItem("Quit", quit_window)
    )
    tray_icon = pystray.Icon("EyeGuard", icon_image, "EyeGuard AI", tray_menu)
    tray_icon.run_detached()

    dpg.setup_dearpygui()
    dpg.set_global_font_scale(1.2)
    
    dpg.show_viewport()
    dpg.set_primary_window("Primary Window", True)
    warn.init()

    # Launch background thread
    worker = threading.Thread(target=camera_worker_thread, args=(cap, h, w), daemon=True)
    worker.start()

    # --- CUSTOM RENDER LOOP ---
    hwnd = None
    frames_rendered = 0
    
    while dpg.is_dearpygui_running() and app_running:
        # 1. Grab the window handle once it actually exists
        if sys.platform == "win32" and hwnd is None:
            hwnd = ctypes.windll.user32.FindWindowW(None, window.title)
            if hwnd:
                # Disable the X button (grays it out) so the user cannot close the app directly
                hmenu = ctypes.windll.user32.GetSystemMenu(hwnd, False)
                if hmenu:
                    ctypes.windll.user32.EnableMenuItem(hmenu, 0xF060, 1)

        # 2. Wait 3 frames to guarantee the OS window has been fully initialized, then hide
        if frames_rendered == 3:
            window.hide()
        if frames_rendered < 10:
            frames_rendered += 1

        # 3. If the user hits the minimize button on the window, intercept it and hide to tray
        if hwnd and sys.platform == "win32":
            if ctypes.windll.user32.IsIconic(hwnd):
                window.hide()

        # Tick the GUI
        dpg.render_dearpygui_frame()
    
    # Cleanup
    app_running = False
    if tray_icon:
        tray_icon.stop()
    dpg.destroy_context()

if __name__ == "__main__":
    main()
