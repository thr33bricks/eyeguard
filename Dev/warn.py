import time
import threading
import eyes_utils
import eyes_actions
import settings

try:
    from plyer import notification
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False
    print("Notice: 'plyer' library not found. OS notifications disabled. Install with: pip install plyer")


class FrameState:
    def __init__(self):
        self.face = eyes_utils.face and not eyes_actions.total_state == "unknown"
        self.screen_distance = eyes_actions.screen_distance
        self.squinting = eyes_actions.squinting

class Second:
    def __init__(self):
        self.valid = False
        self.blinks = 0
        self.screen_distance = 0
        self.squinting = False

# Start time of every new second
second_start = 0

# List of frames for every second
frames_per_second = []

# Fixed length moving window
seconds = []

# If moving windows has enough valid data
valid_data = False

# Average values
avg_blinks_pm = 0
avg_screen_distance = 0
avg_squinting = 0

# Track last notification time to prevent spam
last_blink_warn = 0
last_distance_warn = 0
last_squint_warn = 0

def init():
    reset_second()

def reset_second():
    global second_start, frames_per_second
    
    second_start = time.time()
    eyes_actions.blinks_counter = 0
    frames_per_second = []

def process_second():
    global seconds

    blinks_count = eyes_actions.blinks_counter
    total_frames = len(frames_per_second)
    valid_frames = 0
    distance_sum = 0
    squinting_count = 0
    
    for f in frames_per_second:
        if f.face:
            valid_frames += 1
            distance_sum += f.screen_distance
            squinting_count += 1 if f.squinting else 0

    second = Second()
    if valid_frames / total_frames > settings.SECOND_VALIDITY_THRES:
        second.valid = True
        second.blinks = blinks_count
        second.screen_distance = distance_sum / valid_frames
        second.squinting = (squinting_count / valid_frames > settings.WARN_SQUINTING_THRESHOLD)
    add_second(second)

    calculate_averages()
    print_warnings()
    reset_second()

# Manage adding values to the moving window
def add_second(second: Second):
    global seconds
    seconds.append(second)

    if len(seconds) > settings.SECONDS:
        seconds.pop(0)

def calculate_averages():
    global avg_screen_distance, avg_blinks_pm, avg_squinting, valid_data

    total_seconds = len(seconds)
    valid_seconds = 0
    total_blinks = 0
    distance_sum = 0
    squinting_count = 0

    # Not enough data
    if total_seconds != settings.SECONDS:
        return

    for s in seconds:
        if s.valid:
            valid_seconds += 1
            total_blinks += s.blinks
            distance_sum += s.screen_distance
            squinting_count += 1 if s.squinting else 0

    # Not enough valid data
    if valid_seconds / total_seconds < settings.MOVING_WINDOW_VALIDITY_THRES:
        valid_data = False
        return
    
    valid_data = True
    avg_blinks_pm = (total_blinks / valid_seconds) * 60
    avg_screen_distance = distance_sum / valid_seconds
    avg_squinting = squinting_count / valid_seconds

    if settings.PRINT_AVERAGES:
        eyes_utils.print_verbose(f"AVG Blinks per minute: {avg_blinks_pm:.2f} | AVG Screen distance: {avg_screen_distance:.2f} | AVG Squinting: {avg_squinting:.2f}")

def send_os_notification(title, message):
    if not PLYER_AVAILABLE:
        return
    
    def _notify():
        try:
            notification.notify(
                title=title,
                message=message,
                app_name="EyeGuard",
                timeout=5
            )
        except Exception as e:
            print(f"Failed to send OS notification: {e}")
            
    # Run in a separate thread so it doesn't block the video feed
    threading.Thread(target=_notify, daemon=True).start()

def print_warnings():
    global last_blink_warn, last_distance_warn, last_squint_warn
    if len(seconds) == settings.SECONDS and valid_data:
        cur_time = time.time()
        if avg_blinks_pm < settings.WARN_BLINKS_THRESHOLD:
            if settings.PRINT_EYEGUARD_WARN:
                print("WARNING: Blink more often to prevent dry eyes!")
            if cur_time - last_blink_warn > settings.NOTIFICATION_COOLDOWN:
                send_os_notification("EyeGuard: Low Blink Rate", "Blink more often to prevent dry eyes!")
                last_blink_warn = cur_time
        if avg_screen_distance < settings.WARN_SCREEN_THRESHOLD:
            if settings.PRINT_EYEGUARD_WARN:
                print("WARNING: Keep the screen at least 60 cm away to help prevent eye strain!")
            if cur_time - last_distance_warn > settings.NOTIFICATION_COOLDOWN:
                send_os_notification("EyeGuard: Screen Too Close", "Keep your screen at least 60 cm away to help prevent eye strain!")
                last_distance_warn = cur_time
        if avg_squinting > settings.WARN_SQUINTING_THRESHOLD:
            if settings.PRINT_EYEGUARD_WARN:
                print("WARNING: Squinting detected. Take a break — focus on something 6 meters away for 20 seconds!")
            if cur_time - last_squint_warn > settings.NOTIFICATION_COOLDOWN:
                send_os_notification("EyeGuard: Squinting Detected", "Take a break! Focus on something 6 meters away for 20 seconds.")
                last_squint_warn = cur_time

def update():
    cur_time = time.time()
    cur_frame = FrameState()

    frames_per_second.append(cur_frame)

    if cur_time - second_start >= 1:
        process_second()
