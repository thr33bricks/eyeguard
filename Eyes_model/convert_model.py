import torch
from fastai.vision.all import *
from torch.utils.mobile_optimizer import optimize_for_mobile

# Load your learner
# Note: Ensure the 'timm' library is available in the environment where you run this script
learn = load_learner('eyes_model_1.5_mobilenetv3_small.pkl')
model = learn.model.eval()

# Match your training size: 128x128
dummy_input = torch.randn(1, 3, 128, 128)

# Trace
traced_model = torch.jit.trace(model, dummy_input)

# Optimize for mobile (Lite Interpreter)
optimized_model = optimize_for_mobile(traced_model)

# Save
optimized_model._save_for_lite_interpreter("eyes_model_1.5_mobilenetv3_small.ptl")
print("Model converted and saved as eyes_model.ptl at 128x128 resolution")