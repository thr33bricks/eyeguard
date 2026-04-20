from fastai.vision.all import *
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="fastai.learner")

def classify_eye(img_path, threshold=0.90):
    img = PILImage.create(img_path)
    learn_inf = load_learner('eyes_model_1.0.pkl')
    pred, pred_idx, probs = learn_inf.predict(img)
    
    confidence = probs[pred_idx].item()
    
    if confidence < threshold:
        return "Other / Uncertain", confidence
    else:
        return pred, confidence


# label, conf = classify_eye('open.jpg')
label, conf = classify_eye('eye_open_webcam.jpeg')
print(f"Result: {label} ({conf:.2%})")