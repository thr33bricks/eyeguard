# Multi-label classification on like 100 000 images


from fastai.vision.all import *

path = Path('/home/dan/Programming/Uni/Pavia/Tests/Eyes_model/Eyes_dataset/train')

# 1. We use DataBlock for more control to force Multi-label behavior
dblock = DataBlock(
    blocks=(ImageBlock, MultiCategoryBlock), # MultiCategoryBlock triggers Sigmoid/Logistic logic
    get_items=get_image_files,
    splitter=TrainTestSplitter(test_size=0.2, random_state=42),
    get_y=lambda o: [o.parent.name], # Wraps the folder name in a list to signal 'multi-label'
    item_tfms=Resize(128, method='pad', pad_mode='zeros'),
    batch_tfms=aug_transforms(mult=1.5)
)

dls = dblock.dataloaders(path, bs=32)

# 2. Use accuracy_multi because standard accuracy expects only one winner
# We remove error_rate as it doesn't apply the same way here
learn = vision_learner(dls, resnet34, metrics=[accuracy_multi])

# 3. Fastai will automatically choose BCEWithLogitsLossFlat() 
# (Binary Cross Entropy), which is exactly what your quote suggested.

cbs = [
    EarlyStoppingCallback(monitor='accuracy_multi', patience=3),
    SaveModelCallback(monitor='accuracy_multi', fname='best_eyes_model')
]

learn.fine_tune(10, cbs=cbs)

learn.export('/home/dan/Programming/Uni/Pavia/Tests/Eyes_model/eyes_model_1.2.pkl')