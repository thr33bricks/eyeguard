import customtkinter as ctk
import cv2
from PIL import Image
import time
import mediapipe as mp
import warnings

import settings
import eyes_utils
import eyes_actions
import frame_limiter
import warn


# Suppress MediaPipe protobuf deprecation warnings
warnings.filterwarnings("ignore", category=UserWarning, module="google.protobuf.symbol_database")

fps = 0

class EyeGuardApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Eye Tracker EAR and Classifier - Dashboard")
        self.geometry("1100x650")
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(0, weight=1)
        
        # Setup UI elements
        self.setup_ui()
        
        # Initialize MediaPipe Face Mesh
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=False,
            min_detection_confidence=0.6,
            min_tracking_confidence=0.6
        )
        
        self.cap = eyes_utils.init_cap()
        self.frame_count = 0
        
        # Prevent standalone cv2.imshow popups by default to favor UI video feed
        settings.SHOW_CAMERA_FEED = False
        
        # Initialize warning timing
        warn.init()
        
        # Protocol for safe closing
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Start Video Loop
        self.update_frame()
        
    def setup_ui(self):
        # Video Frame
        self.video_frame = ctk.CTkFrame(self)
        self.video_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.video_label = ctk.CTkLabel(self.video_frame, text="")
        self.video_label.pack(expand=True, fill="both")
        
        # Settings Frame
        self.settings_frame = ctk.CTkFrame(self, width=320)
        self.settings_frame.grid(row=0, column=1, padx=10, pady=10, sticky="ns")
        
        # --- Settings Title ---
        ctk.CTkLabel(self.settings_frame, text="Controls & Settings", font=("Arial", 18, "bold")).pack(pady=15)
        
        # Show Ext. CV2 Windows Switch
        self.cv2_windows_var = ctk.BooleanVar(value=settings.SHOW_CAMERA_FEED)
        self.cv2_windows_switch = ctk.CTkSwitch(
            self.settings_frame, text="Show Extra CV2 Windows", 
            variable=self.cv2_windows_var, command=self.update_settings
        )
        self.cv2_windows_switch.pack(pady=10, padx=20, anchor="w")
        
        # Frame Limiter Switch
        self.limiter_var = ctk.BooleanVar(value=settings.FRAME_LIMITER_ON)
        self.limiter_switch = ctk.CTkSwitch(
            self.settings_frame, text="Frame Limiter (Max 30 FPS)", 
            variable=self.limiter_var, command=self.update_settings
        )
        self.limiter_switch.pack(pady=10, padx=20, anchor="w")
        
        # EAR Threshold
        ctk.CTkLabel(self.settings_frame, text="EAR Threshold").pack(pady=(15, 0), padx=20, anchor="w")
        self.ear_slider = ctk.CTkSlider(self.settings_frame, from_=0.05, to=0.35, command=self.update_settings)
        self.ear_slider.set(settings.EAR_THRESHOLD)
        self.ear_slider.pack(pady=5, padx=20, fill="x")
        self.ear_label = ctk.CTkLabel(self.settings_frame, text=f"{settings.EAR_THRESHOLD:.2f}")
        self.ear_label.pack(pady=0, padx=20, anchor="e")
        
        # Squinting Threshold
        ctk.CTkLabel(self.settings_frame, text="Squinting Threshold").pack(pady=(10, 0), padx=20, anchor="w")
        self.squint_slider = ctk.CTkSlider(self.settings_frame, from_=0.15, to=0.45, command=self.update_settings)
        self.squint_slider.set(settings.SQUINTING_THRESHOLD)
        self.squint_slider.pack(pady=5, padx=20, fill="x")
        self.squint_label = ctk.CTkLabel(self.settings_frame, text=f"{settings.SQUINTING_THRESHOLD:.2f}")
        self.squint_label.pack(pady=0, padx=20, anchor="e")
        
        # Separator Line
        ctk.CTkFrame(self.settings_frame, height=2, fg_color=("gray70", "gray30")).pack(pady=25, padx=20, fill="x")
        
        # --- Dashboard ---
        ctk.CTkLabel(self.settings_frame, text="Live Stats", font=("Arial", 18, "bold")).pack(pady=(0, 15))
        
        self.blink_label = ctk.CTkLabel(self.settings_frame, text="Blinks: 0", font=("Arial", 14))
        self.blink_label.pack(pady=5, padx=20, anchor="w")
        
        self.distance_label = ctk.CTkLabel(self.settings_frame, text="Screen Distance: 0.0 cm", font=("Arial", 14))
        self.distance_label.pack(pady=5, padx=20, anchor="w")
        
        self.squinting_label = ctk.CTkLabel(self.settings_frame, text="Squinting: False", font=("Arial", 14))
        self.squinting_label.pack(pady=5, padx=20, anchor="w")
        
        self.fps_label = ctk.CTkLabel(self.settings_frame, text="FPS: 0", font=("Arial", 14))
        self.fps_label.pack(pady=5, padx=20, anchor="w")

    def update_settings(self, *args):
        settings.SHOW_CAMERA_FEED = self.cv2_windows_var.get()
        settings.FRAME_LIMITER_ON = self.limiter_var.get()
        
        settings.EAR_THRESHOLD = self.ear_slider.get()
        self.ear_label.configure(text=f"{settings.EAR_THRESHOLD:.2f}")
        
        settings.SQUINTING_THRESHOLD = self.squint_slider.get()
        self.squint_label.configure(text=f"{settings.SQUINTING_THRESHOLD:.2f}")

    def update_frame(self):
        global fps
        
        start_time = time.perf_counter()
        success, frame = self.cap.read()
        
        if success:
            if not settings.USE_WEBCAM:
                frame = eyes_utils.resize_for_video(frame)

            frame = cv2.flip(frame, 1)  # Mirror frame
            self.frame_count += 1
            
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_mesh.process(rgb_frame)
            
            eyes_utils.face = False
            if results.multi_face_landmarks:
                eyes_utils.face = True
                for face_landmarks in results.multi_face_landmarks:
                    eyes_utils.update_eye_points(frame, face_landmarks)
                    
                    if self.frame_count % settings.CLASSIFY_EVERY_N_FRAMES == 0:
                        if settings.BATCHED_CLASSIFICATION:
                            eyes_utils.show_eyes_batched(frame)
                        else:
                            eyes_utils.show_eye(frame, "left")
                            eyes_utils.show_eye(frame, "right")
                        self.frame_count = 0
                        
                    eyes_utils.calculate_ear()
                    eyes_utils.draw_ui_main_frame(frame)

            eyes_actions.update()
            warn.update()

            # Process frame events required to keep extra cv2 windows (if enabled) responsive
            if settings.SHOW_CAMERA_FEED:
                cv2.waitKey(1)

            self.blink_label.configure(text=f"Blinks: {eyes_actions.inf_blinks_counter}")
            self.distance_label.configure(text=f"Screen Distance: {eyes_actions.screen_distance:.2f} cm")
            self.squinting_label.configure(text=f"Squinting: {eyes_actions.squinting}")
            self.fps_label.configure(text=f"FPS: {fps:.1f}")

            # Display Main Feed inside Tkinter
            # Convert to RGB array for PIL Image parsing
            display_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(display_frame)
            h, w, _ = display_frame.shape
            ctk_img = ctk.CTkImage(light_image=img, size=(w, h))
            self.video_label.configure(image=ctk_img)

        end_time = time.perf_counter()
        frame_limiter.limit(end_time - start_time)

        # Metrics Updates
        total_frame_time = time.perf_counter() - start_time
        fps = 1 / total_frame_time if total_frame_time > 0 else 0

        # Recursively schedule the next frame update (10 ms standard delay)
        self.after(10, self.update_frame)
        
    def on_closing(self):
        self.cap.release()
        self.face_mesh.close()
        cv2.destroyAllWindows()
        self.destroy()

if __name__ == "__main__":
    ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
    ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"
    
    app = EyeGuardApp()
    app.mainloop()
