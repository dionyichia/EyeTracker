# EyeTracker

A lightweight, robust eye tracker system. This system is used as part of pre-assesessment preparation for patients undergoing the Humphrey Visual Field Test.  

## Installation

## Usage
1. Run the arduino script from the arduino IDE
2. Run the script, using run "python .\OrloskyPupilDetector.py" from terminal. 


A test video (eye_test.mp4) is included in the root directory for testing. Algorithm details are explained here: https://www.youtube.com/watch?v=bL92JUBG8xw


Requirements:
- A Python environment
- An Arduino environment
- An Ardunion
- A pan-tilt servo, 

Packages
- numpy
- opencv

Assumptions
- Works best with 640x480 videos. Images will be cropped to size equally horizontally/vertically if aspect ratio is not 4:3.
- The image must be that of the entire eye. Dark regions in the corners of the image (e.g. VR display lens borders) should be cropped. 
- 



## Citations
This project was adapted from Jason Orlosky's Eye Tracker https://github.com/JEOresearch/EyeTracker/
