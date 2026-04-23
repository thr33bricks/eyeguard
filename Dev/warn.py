import time
import eyes_utils
import eyes_actions
import settings


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

# Average values
avg_blinks_pm = 0
avg_screen_distance = 0
avg_squinting = 0


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
    global avg_screen_distance, avg_blinks_pm, avg_squinting

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
        return
    
    avg_blinks_pm = (total_blinks / valid_seconds) * 60
    avg_screen_distance = distance_sum / valid_seconds
    avg_squinting = squinting_count / valid_seconds

    if settings.PRINT_AVERAGES:
        eyes_utils.print_verbose(f"AVG Blinks per minute: {avg_blinks_pm:.2f} | AVG Screen distance: {avg_screen_distance:.2f} | AVG Squinting: {avg_squinting:.2f}")

def print_warnings():
    if settings.PRINT_EYEGUARD_WARN and len(seconds) == settings.SECONDS:
        if avg_blinks_pm < settings.WARN_BLINKS_THRESHOLD:
            print("WARNING: Blink more often to prevent dry eyes!")
        if avg_screen_distance < settings.WARN_SCREEN_THRESHOLD:
            print("WARNING: Keep your phone at least 30 cm away to help prevent eye strain!")
        if avg_squinting > settings.WARN_SQUINTING_THRESHOLD:
            print("WARNING: Squinting detected. Take a break — focus on something 6 meters away for 20 seconds!")

def update():
    cur_time = time.time()
    cur_frame = FrameState()

    frames_per_second.append(cur_frame)

    if cur_time - second_start >= 1:
        process_second()
