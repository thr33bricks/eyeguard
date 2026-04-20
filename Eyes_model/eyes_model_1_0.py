# Open and closed eyes on like 2000 images

from fastai.vision.all import *

path = Path('/home/dan/Programming/Uni/Pavia/Tests/Eyes_model/Eyes_dataset/test')

dls = ImageDataLoaders.from_folder(
    path, 
    valid_pct=0.2, 
    seed=42,
    bs=32,
    # Use 128 since your source is 90x90
    item_tfms=Resize(128, method='pad', pad_mode='zeros'), 
    batch_tfms=aug_transforms(mult=1.5) # Stronger augmentation helps with small images
)

learn = vision_learner(dls, resnet34, metrics=error_rate)
learn.fine_tune(2)
learn.export('/home/dan/Programming/Uni/Pavia/Tests/Eyes_model/eyes_model_1.0.pkl')
