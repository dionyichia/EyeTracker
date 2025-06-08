# EyeTracker

A lightweight, robust eye-tracking system used as part of the pre-assessment preparation for patients undergoing the Humphrey Visual Field Test.

## Installation

Requirements:
- Python 3.x
- Necessary Python libraries (listed below)
- Arduino IDE
- An Ardunio
- Necessary Arduino modules (listed below)

Packages
- numpy
- opencv

### Setup Instructions
1. Clone this repository:
   ```bash
   git clone https://github.com/your-repo/EyeTracker.git
   cd EyeTracker

2. Install the required Python packages:
   ```bash
   pip install numpy opencv-python

3. Upload the Arduino script using the Arduino IDE.

### Usage
1. Run the arduino script from the arduino IDE
2. Run the script, using run "python .\OrloskyPupilDetector.py" from terminal. 

A test video (eye_test.mp4) is included in the root directory for testing. 

**Change the input_method under select_video function, to 1 and rerun script. Remember to change zoom factor.

Assumptions
- Works best with 640x480 videos. Images will be cropped to size equally horizontally/vertically if aspect ratio is not 4:3.
- The image must be that of the entire eye. Dark regions in the corners of the image (e.g. VR display lens borders) should be cropped. 

### Booth Diagram:

### Circuit Diagram:

## Algorithim Explaination

Eye Tracking
1. Sparse Sampling for darkest point in the image.
2. Binary Thresholding to idenitfy pupil.
3. Cascaded Thresholding with three different threshold values.
4. Fit and elispce to the the pupil in the thresholded images
5. Select best of three thresholded images
6. Find all contour points of the thresholded pupil
7. Denoising contour points to include only keep those that point inwards. 
    - This is important as the shape formed by the contour points may contain anormalies. These arise when there is an reflection or eyelash obstructing the pupil
8. Fit a eslipce to the final contour points in the image

Confidence-based Correction
- A filter to reduce switching between binary threshold value. This reduces the spasms in the final eclipse drawn.
1. If the best binary threshold value used in the current frame is different from the one used in the previous frame, check whether the difference in the 'goodness' of the thresholded surpasses a confidence margin. 
2. If yes, switch to new threshold value, else, default to previous threshold value

Lock Pupil Position Function
- A function to save a pupil's relative position in the current frame and signal if the pupil exceeds a threshold value for euclidian distance in subseequent frames (lockpos threshold),

Haptic Feedback Tracker
- A script to send signals to the arduino if pupil exceeds euclid threshold. 


## Citations
This project was adapted from Jason Orlosky's Eye Tracker [https://github.com/JEOresearch/EyeTracker/]

Algorithm details are further explained [here](https://www.youtube.com/watch?v=bL92JUBG8xw).
