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
#
# I first tried using EAR(Eye aspect ratio) based on facial landmarks but it was unreliable
# because it couldnt detect occluded eyes and I could put an object in front of my eye
# and it would still be detected as open/closed based on EAR
#
# Then I decided I should use a model that takes the eye crop as input and classifies it as open, 
# closed or occluded(unknown).
#
# I made reliable blink detection by using this model and defining open eyes state as both eyes open,
# and the same for closed eyes. If one of the eyes is unknown then eyes state is unknown.
# If at least one of the eyes has an uncertain classification a counter is increased and
# if the counter reaches a certain threshold the eye is considered unknown. 
# This way I can ignore uncertain classifications.


# For squinting I calculate EAR with the formula (|p1 - p6| + |p3 - p5|) / 2 * |p1 - p4|
# Which basically means - get average of 2 verticals and divide by horizontal.
# I do this for both eyes and take average
#
# Borderline for me is around 0.25, below that I am squinting
#
# Research
# https://www.mdpi.com/2079-9292/11/19/3183


# I will use distance between eye centres (in pixels) compared to screen resolution to evaluate 
# distance between user and screen.

# Currently I am recording videos on my redmi note 7 looking at the screen from distances between 15cm
# and 65 cm with an interval of 5cm and I will use this to make an equasion that will estimate distance
# between user and screen based on eye distance in pixels and resolution.

# But I will have to test with other cameras too because focal length will affect the results.
# Also head rotation will affect eye distance




# Research links distance to screen, eye strain
# 
# https://www.zeiss.com/vision-care/en/eye-health-and-care/health-prevention/digital-eye-strain-how-different-screens-affect-different-people.html
# https://www.aoa.org/healthy-eyes/eye-and-vision-conditions/computer-vision-syndrome
# https://www.aao.org/eye-health/tips-prevention/computer-usage
# https://pubmed.ncbi.nlm.nih.gov/27716998/
# https://www.jstage.jst.go.jp/article/jpts/28/1/28_jpts-2015-817/_article
# https://www.nature.com/articles/s41433-023-02781-9
#
#
# Normal blinking distance > 35 cm to reduce eye strain
# Give notifications if distance is less than 30 cm and warn if distance is less than 20 cm
# 

# Research links blinking and eye strain
#
# https://pmc.ncbi.nlm.nih.gov/articles/PMC9927758/
#
# Blink rate 7 or below blinks per minute is considered low and user should be notified to blink more often
#

# Squinting and eye strain
# 
# https://www.hra.nhs.uk/planning-and-improving-research/application-summaries/research-summaries/focusing-control-in-squint-and-eye-strain/
# https://scienceinsights.org/how-does-squinting-help-you-see-better/
# https://link.springer.com/article/10.1186/s12886-019-1297-5
# https://pubmed.ncbi.nlm.nih.gov/14627939/
#
# If squinting is detected for more than 5 seconds continuously, user should be notified to 
# relax their eyes, take a walk or sth
#



# Maybe add a feature that tracks if you watched the screen for more than 20 minutes without a break.




# Projects to check if better than mine
# https://github.com/codedByCan/Eye_Blink_Detection
# https://github.com/Pushtogithub23/Eye-Blink-Detection-using-MediaPipe-and-OpenCV
# https://github.com/Shakirsadiq6/Blink_Detection_Python