# Same as eyes_model_1_4.py but for mobile

import timm
from fastai.vision.all import *

path = Path('/home/dan/Programming/Uni/Pavia/Tests/Eyes_model/Eyes_dataset/train')

# 1. Load Data
dls = ImageDataLoaders.from_folder(
    path, 
    valid_pct=0.2, 
    seed=42,
    bs=32,
    item_tfms=Resize(128, method='pad', pad_mode='zeros'), 
    batch_tfms=aug_transforms(mult=1.5) 
)

# 2. Create Learner
# 'mobilenetv3_large_100', 'mobilenetv3_small_100'
learn = vision_learner(dls, 'mobilenetv3_small_100', metrics=[error_rate, accuracy])

# 3. Handle Class Imbalance (Weighting the 'unknown' folder)
# Order matches dls.vocab: ['closed', 'open', 'unknown']
counts = [39987, 40464, 912] 
weights = tensor([1/c for c in counts])
weights = weights / weights.sum()

# Assign the weighted loss function to the learner
# .cuda() ensures the weights are on the GPU alongside your model
learn.loss_func = CrossEntropyLossFlat(weight=weights.cuda())

# 4. Training Callbacks
cbs = [
    EarlyStoppingCallback(monitor='error_rate', patience=3),
    SaveModelCallback(monitor='error_rate', fname='best_eyes_model')
]

# 5. Train
learn.fine_tune(10, cbs=cbs)

# 6. Export
learn.export('/home/dan/Programming/Uni/Pavia/Tests/Eyes_model/eyes_model_1.5.pkl')