import time
import settings

frame_time = 1.0 / settings.MAX_FPS

def limit(cur_frame_time):
    if not settings.FRAME_LIMITER_ON:
        return
    
    sleep_time = frame_time - cur_frame_time
    if sleep_time > 0:
        time.sleep(sleep_time)