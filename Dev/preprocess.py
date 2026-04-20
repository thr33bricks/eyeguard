import cv2
import settings

def is_blurry(frame, threshold=1000.0):
    """
    Detect if an image is blurry using the Laplacian variance method.

    Args:
        frame (numpy.ndarray): The input image.
        threshold (float): Variance threshold below which the image is considered blurry.

    Returns:
        bool: True if the image is blurry, False otherwise.
        float: The variance of the Laplacian.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    cv2.imshow('Laplacian', laplacian)
    variance = laplacian.var()
    if settings.PRINT_FRAME_VARIANCE:
        print(f"Frame variance: {variance:.2f}")

    # Determine if the image is blurry
    return variance < threshold

def is_useful(frame):
    """
    Determine if an image is useful based on its sharpness.

    Args:
        frame (numpy.ndarray): The input image.

    Returns:
        bool: True if the image is useful, False otherwise.
    """
    return not is_blurry(frame, settings.BLURRY_FRAME_THRESHOLD)