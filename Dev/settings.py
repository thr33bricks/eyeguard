# CLIP_DURATION = 10 # In seconds
# CLIP_FPS = 30.0
# CLIP_NAME = "output.mp4"

MAIN_WINDOW_TITLE = 'Eye Tracker EAR and Classifier'
PRINT_EYEGUARD_WARN = True
PRINT_VERBOSE = True
PRINT_FRAME_TIME = True
PRINT_CLASSIFIER_RESULTS = False
PRINT_EYE_ACTION_INFO = False
PRINT_FRAME_VARIANCE = False
PRINT_AVERAGES = False

BATCHED_CLASSIFICATION = True

USE_WEBCAM = True
# BLURRY_FRAME_THRESHOLD = 10.0
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
# VIDEO_PATH = 'Dev/video/note7_5blinks_eye_easy.mp4'
# VIDEO_PATH = 'Dev/video/note7_5blinks_hard.mp4'
# VIDEO_PATH = 'Dev/video/note7_9blinks_hard.mp4'
VIDEO_PATH = 'Dev/video/note7_instagram.mp4'
# VIDEO_PATH = 'Dev/video/note7_instagram_squinting.mp4'
# VIDEO_PATH = 'Dev/video/note7_instagram_squinting_2.mp4'

# VIDEO_PATH = 'Dev/video/user_to_screen_distance/note7_60cm.mp4'

VIDEO_WIDTH = 480

EAR_THRESHOLD = 0.1
FACE_HEIGHT = 300
EYE_CROP_ASPECT_RATIO = 1.7
EYE_MODEL_NAME = 'eyes_model_1.5_mobilenetv3_small.pkl'
EYE_MODEL_UNCERT_THRES = 0.94

# Used for blink action
# A successful classification = open, closed, unknown
# An unsuccessful classification = uncertain
MAX_UNSUCCESSFUL_CLASSIFICATIONS = 6

# Used for squinting detection
# squ_val = eye_distance / eye_vertical
SQUINTING_THRESHOLD = 0.24

# Screen distance calibration
SCREEN_DISTANCE_CALIBRATION = -8.0 # -8.0 for laptop webcam, 0.0 for redmi note 7


# The threshold (0-1) that indicates if the data collected for one second is valid
# It is valid if a face is present, both eyes are open or both are closed
SECOND_VALIDITY_THRES = 0.7

# The threshold (0-1) that indicates what part of the seconds collected in the moving 
# window should be valid to consider the data for warnings
MOVING_WINDOW_VALIDITY_THRES = 0.7

# The number of seconds for the warnings moving window
SECONDS = 10

# Squinting threshold (0-1) indicates what part of the valid frames in
# a second should be squinting to mark the whole second as squinting
SECOND_SQUINTING_THRESHOLD = 0.7


# Warnings
# Blinks per minute
WARN_BLINKS_THRESHOLD = 7

# User to screen distance (cm)
WARN_SCREEN_THRESHOLD = 30

# The threshold (0-1) that indicates what part of the seconds in the
# moving window are squinting
WARN_SQUINTING_THRESHOLD = 0.8