import eyes_utils
import settings


blinks_counter = 0

left_eye_state = "unknown"
right_eye_state = "unknown"
total_state = "unknown"
last_total_state = "unknown"

# eye states are open, closed and unknown so
# uncertain states are unsuccessful and they are ignored
# If an eye receives an unsuccessful classification a certeain number
# of times in a row it is considered unknown
left_unsuccessful = 0
right_unsuccessful = 0

# Distance between eyes
eye_distance = 0.0

# Squinting
squinting = False

# Screen distance
screen_distance = 0.0


def update_eyes_states():
    global left_unsuccessful, right_unsuccessful, left_eye_state, right_eye_state
    if eyes_utils.left_eye_state == "uncertain":
        left_unsuccessful += 1
    else:
        left_eye_state = eyes_utils.left_eye_state
        left_unsuccessful = 0

    if eyes_utils.right_eye_state == "uncertain":
        right_unsuccessful += 1
    else:
        right_eye_state = eyes_utils.right_eye_state
        right_unsuccessful = 0

    if left_unsuccessful >= eyes_utils.settings.MAX_UNSUCCESSFUL_CLASSIFICATIONS:
        left_eye_state = "unknown"
    if right_unsuccessful >= eyes_utils.settings.MAX_UNSUCCESSFUL_CLASSIFICATIONS:
        right_eye_state = "unknown"

def update_total_state():
    global last_total_state, total_state
    last_total_state = total_state

    if left_eye_state == "unknown" or right_eye_state == "unknown":
        total_state = "unknown"

    if left_eye_state == "open" and right_eye_state == "open":
        total_state = "open"

    if left_eye_state == "closed" and right_eye_state == "closed":
        total_state = "closed"

def update_blinks():
    global blinks_counter
    if total_state == "open" and last_total_state == "closed":
        blinks_counter += 1

def update_eye_distance():
    global eye_distance

    if left_eye_state == "unknown" or right_eye_state == "unknown":
        eye_distance = 0.0
        return

    left_left = eyes_utils.left_eye_pts[0]  # Left corner
    left_right = eyes_utils.left_eye_pts[3]  # Right corner
    left_center = ((left_left[0] + left_right[0]) / 2, (left_left[1] + left_right[1]) / 2)

    right_left = eyes_utils.right_eye_pts[0]  # Left corner
    right_right = eyes_utils.right_eye_pts[3]  # Right corner
    right_center = ((right_left[0] + right_right[0]) / 2, (right_left[1] + right_right[1]) / 2)

    eye_distance = eyes_utils.euclidean(left_center, right_center)

def update_eye_squinting():
    global squinting

    if left_eye_state == "unknown" or right_eye_state == "unknown":
        squinting = None
        return

    squinting = eyes_utils.avg_ear < settings.SQUINTING_THRESHOLD

def update_screen_distance():
    global screen_distance

    if eye_distance == 0.0:
        screen_distance = 0.0
        return

    norm_eye_distance = eye_distance * (480 / settings.VIDEO_WIDTH)
    if norm_eye_distance == 0.0:
        screen_distance = 0.0
        return

    if norm_eye_distance < 20:
        screen_distance = norm_eye_distance / -5 + 300 + settings.SCREEN_DISTANCE_CALIBRATION
    else:
        screen_distance = 4000 / (norm_eye_distance - 2) + settings.SCREEN_DISTANCE_CALIBRATION

def print_info():
     if settings.PRINT_EYE_ACTION_INFO:
        eyes_utils.print_verbose(f"Blinks count: {blinks_counter} | Screen distance: {screen_distance:.2f} cm | Squinting: {squinting}")

def update():
    update_eyes_states()
    update_total_state()
    update_blinks()
    update_eye_distance()
    update_eye_squinting()
    update_screen_distance()
    print_info()
