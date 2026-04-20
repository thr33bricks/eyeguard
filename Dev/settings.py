# CLIP_DURATION = 10 # In seconds
# CLIP_FPS = 30.0
# CLIP_NAME = "output.mp4"

MAIN_WINDOW_TITLE = 'Eye Tracker EAR and Classifier'
PRINT_VERBOSE = True
PRINT_FRAME_TIME = False
PRINT_CLASSIFIER_RESULTS = False
PRINT_EYE_ACTION_INFO = False
PRINT_FRAME_VARIANCE = True

BATCHED_CLASSIFICATION = True

USE_WEBCAM = True
BLURRY_FRAME_THRESHOLD = 5.0
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
# VIDEO_PATH = 'Dev/video/note7_5blinks_eye_easy.mp4'
# VIDEO_PATH = 'Dev/video/note7_5blinks_hard.mp4'
# VIDEO_PATH = 'Dev/video/note7_9blinks_hard.mp4'
# VIDEO_PATH = 'Dev/video/note7_instagram.mp4'
# VIDEO_PATH = 'Dev/video/note7_instagram_squinting.mp4'
# VIDEO_PATH = 'Dev/video/note7_instagram_squinting_2.mp4'

VIDEO_PATH = 'Dev/video/user_to_screen_distance/note7_60cm.mp4'

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
SQUINTING_THRESHOLD = 10

# Screen distance calibration
SCREEN_DISTANCE_CALIBRATION = -8.0 # -8.0 for laptop webcam, 0.0 for redmi note 7