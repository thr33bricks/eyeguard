# model 1.0 - 2 epochs fine tuning with resnet34 on 2000 images
# model 1.1 - 10 epochs fine tuning with resnet34 and early stopping on 2000 images
# model 1.2 - 10 epochs fine tuning with resnet34 and early stopping on 100 000 images
# model 1.3 - ???
# model 1.4 - 10 epochs fine tuning with resnet34, early stopping and weighted loss function on 81000 images
#  - here I trained the model to recognise occluded eyes as unknown state with my own dataset of 1000 images
#  - of occluded eyes with fingers, fists, different objects all in different lighting conditions and angles
# model 1.5 - 10 epochs fine tuning with mobilenetv3_small
#  - same as 1.4 but with lighter model

# I have to explain how classify_eye, classify_eye_fast and classify_eyes_batched work
# And how I found the fastest version

# Explain that I tested with webcam and with videos from an actual smartphone and explain
# that the videos had better results because of the nature of the smartphone,
# that users make the screen perpendicular to their face and the eyes dont appear looking downwards as much as with a webcam, 
# where users tend to look downwards more often and the angle is less optimal for the classifier

# Explain that the eye_crop is cut from the original frame based on the eye landmarks and
# is cut based on head rotation

# I first tried using EAR(Eye aspect ratio) based on facial landmarks but it was unreliable
# because it couldnt detect occluded eyes and I could put an object in front of my eye
# and it would still be detected as open/closed based on EAR

# Then I decided I should use a model that takes the eye crop as input and classifies it as open, 
# closed or occluded(unknown).

# I made reliable blink detection by using this model and defining open eyes state as both eyes open,
# and the same for closed eyes. If one of the eyes is unknown then eyes state is unknown.
# If at least one of the eyes has an uncertain classification a counter is increased and
# if the counter reaches a certain threshold the eye is considered unknown. 
# This way I can ignore uncertain classifications.

# I measured the distance between eye centres compared to eye vertical distance and found a
# threshold for squ_val = eye_distance / eye_vertical that indicates squinting. This one will vary from person
# to person, especially if you are asian. :):):)

# So the appropriate threshold should be around 10

# I will use distance between eye centres (in pixels) compared to screen resolution to evaluate 
# distance between user and screen.

# Currently I am recording videos on my redmi note 7 looking at the screen from distances between 15cm
# and 65 cm with an interval of 5cm and I will use this to make an equasion that will estimate distance
# between user and screen based on eye distance in pixels and resolution.

# But I will have to test with other cameras too because focal length will affect the results.
# Also head rotation will affect eye distance



