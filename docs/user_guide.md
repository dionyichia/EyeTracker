## Usage
1. Run the arduino script from the arduino IDE
2. Run the script, using run "python .\OrloskyPupilDetector.py" from terminal. 

A test video (eye_test.mp4) is included in the root directory for testing. 

**Change the input_method under select_video function, to 1 and rerun script. Remember to change zoom factor.

Assumptions
- Works best with 640x480 videos. Images will be cropped to size equally horizontally/vertically if aspect ratio is not 4:3.
- The image must be that of the entire eye. Dark regions in the corners of the image (e.g. VR display lens borders) should be cropped. 
