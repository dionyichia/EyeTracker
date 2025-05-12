import cv2
import numpy as np
import random
import math
import tkinter as tk
import os
from tkinter import filedialog
import matplotlib.pyplot as plt
import time
from core.arduino_tracker import ArduinoTracker
from core.pupil_tracker_utils import EyeTrackerUtils

class EyeTracker():
    """Class for tracking eye pupil position using OpenCV"""
    
    # Video input config params, for debugging and demonstration
    CAMERA_FEED = 0
    TEST_VIDEO = 1

    # Command constants (single-byte for efficiency)
    CMD_WITHIN_THRESHOLD = b'\x06'  # Within threshold signal (0x06)
    CMD_OUT_OF_THRESHOLD = b'\x07'  # Out of threshold signal (0x07)
    
    def __init__(self, arduino_tracker=None):
        """Initialize the eye tracker"""
        self.tracker = arduino_tracker
        self.cap = None

        # Video input path 
        self.vid_input = self.CAMERA_FEED
        
        # Configuration parameters
        # self.threshold_value = 15  # Default threshold value (no clue)
        self.zoom_factor = 1 # Video feed zoom factor
        self.lockpos_threshold = 48 # Allowable distance between pupil position and initial calibrated position. (Euclid dist)
        self.threshold_switch_confidence_margin = 2
        
        # State tracking
        self.pupil_center_pos = None # Tracks the center of the pupil (center of darkest area)
        self.is_position_locked = False # False if not calibrated, i.e. Locked when user's pupil is at the correct position
        self.locked_position = -1 # Tracks the locked position coordinates, the calibrated position.
        self.distance_between_pupilpos_and_lockpos = 0 # Tracks the distance between the pupil pos in the current frame with the initial calibrated position
        self.is_pupil_pos_within_threshold = True # True if the distance between the pupil pos current frame within the set threshold. i.e. False if too far, user is looking away
        self.prev_command = 'L'
        
        self.prev_threshold_index = 0 # Tracks the grayscale threshold used. There are 3 grayscale thresholds used, for differing degree of strictness. 1 - light, 2 - medium, 3 - heavy (strict). The threshold used is dynamically determined to give best fitted pupil.
        
        # Initialize camera
        self._initialize_camera()

    def process_frames(self, prev_threshold_index, threshold_swtich_confidence_margin, 
                    thresholded_image_strict, thresholded_image_medium, thresholded_image_relaxed, 
                    frame, gray_frame
                    ):
        """
        Process frames but don't show OpenCV windows
        """
        final_rotated_rect = ((0,0),(0,0),0)

        image_array = [thresholded_image_relaxed, thresholded_image_medium, thresholded_image_strict] #holds images
        name_array = ["relaxed", "medium", "strict"] #for naming windows
        final_image = image_array[0] #holds return array
        final_contours = [] #holds final contours
        ellipse_reduced_contours = [] #holds an array of the best contour points from the fitting process
        goodness = [] # goodness arr for to store goodness for all ellipse
        best_array = 0 
        kernel_size = 5  # Size of the kernel (5x5)
        kernel = np.ones((kernel_size, kernel_size), np.uint8)
        gray_copy1 = gray_frame.copy()
        gray_copy2 = gray_frame.copy()
        gray_copy3 = gray_frame.copy()
        gray_copies = [gray_copy1, gray_copy2, gray_copy3]
        final_goodness = 0

        best_image_threshold_index = 1
        
        #iterate through binary images and see which fits the ellipse best
        for i in range(1,4):
            # Dilate the binary image
            dilated_image = cv2.dilate(image_array[i-1], kernel, iterations=2)#medium
            
            # Find contours
            contours, hierarchy = cv2.findContours(dilated_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Create an empty image to draw contours
            contour_img2 = np.zeros_like(dilated_image)
            reduced_contours = EyeTrackerUtils.filter_contours_by_area_and_return_largest(contours, 1000, 3)

            if len(reduced_contours) > 0 and len(reduced_contours[0]) > 5:
                current_goodness = EyeTrackerUtils.check_ellipse_goodness(dilated_image, reduced_contours[0])
                gray_copy = gray_frame.copy()
                cv2.drawContours(gray_copies[i-1], reduced_contours, -1, (255), 1)
                ellipse = cv2.fitEllipse(reduced_contours[0])
                    
                #in total pixels, first element is pixel total, next is ratio
                total_pixels = EyeTrackerUtils.check_contour_pixels(reduced_contours[0], dilated_image.shape)                 
                
                cv2.ellipse(gray_copies[i-1], ellipse, (255, 0, 0), 2)  # Draw with specified color and thickness of 2
                font = cv2.FONT_HERSHEY_SIMPLEX  # Font type
                
                current = current_goodness[0]*total_pixels[0]*total_pixels[0]*total_pixels[1]
            
                goodness.append(current)
                ellipse_reduced_contours.append(total_pixels[2])
                final_contours.append(reduced_contours)

                # If the current iteration has the best goodness set it as best_image_threshold_index
                if current > 0 and current == max(current, final_goodness): 
                    best_image_threshold_index = i-1
                    final_goodness = current
                    
            else:
                goodness.append(0)
                ellipse_reduced_contours.append([])
                final_contours.append([])

            
        # Confidence-Based Threshold Switching, to prevent flickering caused by toggling between thresholds, only switch if goodness difference btw thres is significant
        # If the threshold index used in the previous frame and cur frame are not the same, apply confidence check
        if best_image_threshold_index != prev_threshold_index:
            # Assign the current goodness of prev_threshold_index to prev_goodness
            prev_goodness = goodness[prev_threshold_index] if prev_threshold_index >= 0 else 0
        
            # If the best_image index's goodness is better than prev_goodness by the stipluted margin, switch images, else dont 
            if goodness[best_image_threshold_index] > prev_goodness * (1 + threshold_swtich_confidence_margin):
                print("Changed prev_threshold_index ", prev_threshold_index, " prev_goodness ", prev_goodness, " cur index ", best_image_threshold_index, " goodness ", goodness[best_image_threshold_index])
                prev_threshold_index = best_image_threshold_index


        ellipse_reduced_contours = ellipse_reduced_contours[prev_threshold_index]
        final_contours = final_contours[prev_threshold_index]
        final_image = dilated_image

        # If darkest point position hover around a particular location for more than 5 seconds, or if "L" is pressed then lockpos
        if self.is_position_locked:
                print("lock_mode_on running,  track_darkest_pt ", self.locked_position,  " darkest_point ", self.pupil_center_pos)
                if (self.locked_position == -1):
                    print("Calibration Error:, pupil position not calibrated!")
                else:
                    self.distance_between_pupilpos_and_lockpos =  math.dist(self.locked_position, self.pupil_center_pos) 
                    print("mathing, euclid dist: ", self.distance_between_pupilpos_and_lockpos)
                    frame = self.lockpos(frame, final_contours)

        test_frame = frame.copy()
        
        final_contours = [EyeTrackerUtils.optimize_contours_by_angle(final_contours, gray_frame)]
        
        if final_contours and not isinstance(final_contours[0], list) and len(final_contours[0] > 5):
            ellipse = cv2.fitEllipse(final_contours[0])
            final_rotated_rect = ellipse
            center_x, center_y = map(int, ellipse[0])
            cv2.circle(test_frame, (center_x, center_y), 3, (255, 255, 0), -1)
            
            # Add instructions as overlay text
            cv2.putText(test_frame, "SPACE = play/pause", (10,410), cv2.FONT_HERSHEY_SIMPLEX, .55, (255,90,30), 2)
            cv2.putText(test_frame, "Q      = quit", (10,430), cv2.FONT_HERSHEY_SIMPLEX, .55, (255,90,30), 2)
            cv2.putText(test_frame, "D      = show debug", (10,450), cv2.FONT_HERSHEY_SIMPLEX, .55, (255,90,30), 2)

            if self.is_position_locked == False:
                cv2.ellipse(test_frame, ellipse, (255, 0, 0), 2)

        # Don't display the OpenCV window
        # if render_cv_window:
        #     cv2.imshow('best_thresholded_image_contours_on_frame', test_frame)
        
        # Create an empty image to draw contours
        contour_img3 = np.zeros_like(image_array[i-1])
        
        if len(final_contours[0]) >= 5:
            contour = np.array(final_contours[0], dtype=np.int32).reshape((-1, 1, 2)) #format for cv2.fitEllipse
            ellipse = cv2.fitEllipse(contour) # Fit ellipse
            cv2.ellipse(gray_frame, ellipse, (255,255,255), 2)  # Draw with white color and thickness of 2

        # Return the test_frame instead which has all the visualizations
        return test_frame, final_rotated_rect, final_contours, prev_threshold_index

    # Finds the pupil in an individual frame and returns the center point
    def _process_single_frame(self, frame):
        """Process a single frame with all your existing algorithms"""
        if frame is None:
            return None
            
        # Crop and resize frame
        frame = EyeTrackerUtils.crop_to_aspect_ratio(frame)
        
        # Apply zoom effect if needed
        if self.zoom_factor > 1:
            frame = EyeTrackerUtils.zoom_frame(frame, self.zoom_factor)
        
        # Find the darkest point (pupil center)
        self.pupil_center_pos = EyeTrackerUtils.get_darkest_area(frame)
        if self.pupil_center_pos is None:
            return frame  # Return original frame if no darkest point found
        
        # Convert to grayscale
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        darkest_pixel_value = gray_frame[self.pupil_center_pos[1], self.pupil_center_pos[0]]
        
        # Apply thresholding at different levels (from your original code)
        thresholded_image_strict = EyeTrackerUtils.apply_binary_threshold(gray_frame, darkest_pixel_value, 5)
        thresholded_image_strict = EyeTrackerUtils.mask_outside_square(thresholded_image_strict, self.pupil_center_pos, 250)
        
        thresholded_image_medium = EyeTrackerUtils.apply_binary_threshold(gray_frame, darkest_pixel_value, 15)
        thresholded_image_medium = EyeTrackerUtils.mask_outside_square(thresholded_image_medium, self.pupil_center_pos, 250)
        
        thresholded_image_relaxed = EyeTrackerUtils.apply_binary_threshold(gray_frame, darkest_pixel_value, 25)
        thresholded_image_relaxed = EyeTrackerUtils.mask_outside_square(thresholded_image_relaxed, self.pupil_center_pos, 250)
        
        # Check if we have a locked position to track
        self.locked_position = self.locked_position if self.is_position_locked else -1
        
        # Process frames with your existing method - get the processed frame with visualizations
        processed_frame, pupil_rotated_rect, final_contours, threshold_index = self.process_frames(
            self.prev_threshold_index, 
            self.threshold_switch_confidence_margin,
            thresholded_image_strict, 
            thresholded_image_medium, 
            thresholded_image_relaxed,
            frame, 
            gray_frame,
        )
        
        # Update threshold index for next frame
        self.prev_threshold_index = threshold_index
        
        # Return the processed frame with visualizations
        return processed_frame

    def get_processed_frame(self):
        """Get current frame with processing applied - called by GUI timer"""
        if not self.cap or not self.cap.isOpened():
            return None
        
        ret, frame = self.cap.read()
        if not ret:
            return None
        
        # Apply all processing steps and return the processed frame
        processed_frame = self._process_single_frame(frame)
        return processed_frame

    def process_video(self, video_path, input_method, zoom_factor=5, zoom_center=None, arduino_port=None, threshold_swtich_confidence_margin=1):
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Codec for MP4 format
        out = cv2.VideoWriter('C:/Storage/Source Videos/output_video.mp4', fourcc, 30.0, (640, 480))  # Output video filename, codec, frame rate, and frame size

        if input_method == 1:
            cap = cv2.VideoCapture(video_path)
        elif input_method == 2:
            cap = cv2.VideoCapture(0)  # Camera input
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 2048) # Resolution set to 2k (2048, 1080)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
            cap.set(cv2.CAP_PROP_EXPOSURE, 0)
        else:
            print("Invalid video source.")
            return

        if not cap.isOpened():
            print("Error: Could not open video.")
            return
        
        self.is_position_locked = False
        self.locked_position = -1

        # Track last index used, use to implement Confidence-Based Threshold Switching btw threshold to reduce flickering
        prev_threshold_index = 0

        # Track last command sent to arduino, only send command if there is a change in command
        self.prev_command = 'L'

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Crop and resize frame
            frame = EyeTrackerUtils.crop_to_aspect_ratio(frame)

            # Apply zoom effect
            frame = EyeTrackerUtils.zoom_frame(frame, zoom_factor, zoom_center)

            # Find the darkest point
            self.pupil_center_pos = self.get_darkest_area(frame)

            # Convert to grayscale to handle pixel value operations
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            darkest_pixel_value = gray_frame[self.pupil_center_pos[1], self.pupil_center_pos[0]]
            
            # Apply thresholding operations at different levels
            thresholded_image_strict = EyeTrackerUtils.apply_binary_threshold(gray_frame, darkest_pixel_value, 5)  # lite
            thresholded_image_strict = EyeTrackerUtils.mask_outside_square(thresholded_image_strict, self.pupil_center_pos, 250)

            thresholded_image_medium = EyeTrackerUtils.apply_binary_threshold(gray_frame, darkest_pixel_value, 15)  # medium
            thresholded_image_medium = EyeTrackerUtils.mask_outside_square(thresholded_image_medium, self.pupil_center_pos, 250)
            
            thresholded_image_relaxed = EyeTrackerUtils.apply_binary_threshold(gray_frame, darkest_pixel_value, 25)  # heavy
            thresholded_image_relaxed = EyeTrackerUtils.mask_outside_square(thresholded_image_relaxed, self.pupil_center_pos, 250)
            
            # Take the three images thresholded at different levels and process them
            print("lock_mode ", self.is_position_locked)
            pupil_rotated_rect, final_contours, threshold_index = self.process_frames(prev_threshold_index, threshold_swtich_confidence_margin, thresholded_image_strict, thresholded_image_medium, thresholded_image_relaxed, frame, gray_frame)

            # Set the current threshold being used as the prev threshold index, once image processed.
            prev_threshold_index = threshold_index

            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                break
            elif key == ord(' '):
                while True:
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord(' '):
                        break
                    elif key == ord('q'):
                        break
            if key == ord('l') and not self.is_position_locked:
                print("Setting lock")
                self.locked_position = self.pupil_center_pos
                self.is_position_locked = True
            elif key == ord('l') and self.is_position_locked:
                print("Resetting lock")
                self.locked_position = -1
                self.is_position_locked = False

        arduino_port.close()
        cap.release()
        out.release()
        cv2.destroyAllWindows()

    def _initialize_camera(self):
        """Initialize the webcam"""
        try:
            if self.vid_input:
                self.cap = cv2.VideoCapture(0)  # Use default camera // NOT FIXED need to think of some realtive path maybe idk
            else:
                self.cap = cv2.VideoCapture(0)  # Use default camera

            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_EXPOSURE, 0)
            
            if not self.cap.isOpened():
                print("Error: Could not open camera.")
                return False
            
            return True
        except Exception as e:
            print(f"Camera initialization error: {str(e)}")
            return False

    def lockpos(self, frame, final_contours):
        """Process pupil position and send appropriate commands to Arduino
        
        Args:
            frame: Video frame to process
            final_contours: Detected pupil contours
            distance_between_pupilpos_and_lockpos: Distance of pupil from reference point
            lockpos_threshold: Maximum allowed distance
            
        Returns:
            processed_frame
        """        
        # Only process if we have contours
        if not final_contours:
            return frame
            
        # Check if pupil is within allowed distance from reference point
        if self.distance_between_pupilpos_and_lockpos > self.lockpos_threshold:
            # Pupil is outside threshold - draw red ellipse
            self.is_pupil_pos_within_threshold = False
            frame = EyeTrackerUtils.fit_and_draw_ellipses(frame, final_contours[0], (255, 0, 0))
            command = self.CMD_OUT_OF_THRESHOLD

            
            # Send command to Arduino if tracker is available AND if command is different from previous command (for efficiency) 
            if self.tracker and self.tracker.is_connected() and command != self.prev_command:
                result = self.tracker.send_command(command)

                # Add ack cmd checker??
                
                if result == 1:
                    print("OUT OF THRESHOLD command sent and acknowledged")
                    self.prev_command = command
                elif result == 2:
                    print("Error: Program ended by Arduino")
                    return frame  # Signal to main loop to exit
                else:
                    print("Failed to send OUT OF THRESHOLD command")
                    
            # print("Out of threshold")
        else:
            # Pupil is within threshold - draw green ellipse
            self.is_pupil_pos_within_threshold = True
            frame = EyeTrackerUtils.fit_and_draw_ellipses(frame, final_contours[0], (0, 255, 0))
            command = self.CMD_WITHIN_THRESHOLD
            
            # Send command to Arduino if tracker is available
            if self.tracker and self.tracker.is_connected() and command != self.prev_command:
                result = self.tracker.send_command(command)
                
                if result == 1:
                    print("WITHIN THRESHOLD command sent and acknowledged")
                    self.prev_command = command
                elif result == 2:
                    print("Program ended by Arduino")
                    return frame
                else:
                    print("Failed to send WITHIN THRESHOLD command")
            
        return frame
    
    def set_threshold(self, value):
        """Set the threshold value based on slider in GUI"""
        self.lockpos_threshold = value
    
    def lock_position(self):
        """Lock the current eye position as reference point"""
        if not self.cap or not self.cap.isOpened():
            return
        
        ret, frame = self.cap.read()
        if not ret:
            return
        
        # Find darkest point (pupil center)
        frame = EyeTrackerUtils.crop_to_aspect_ratio(frame)
        if self.zoom_factor > 1:
            frame = EyeTrackerUtils.zoom_frame(frame, self.zoom_factor)
            
        self.locked_position = EyeTrackerUtils.get_darkest_area(frame)
        self.is_position_locked = True
    
    def is_eye_in_position(self):
        """Check if eye is in the calibrated position
        
        Returns:
            bool: True if eye is in position, False otherwise
        """
        if not self.is_position_locked or self.locked_position is None:
            return False
        
        if not self.cap or not self.cap.isOpened():
            return False
        
        ret, frame = self.cap.read()
        if not ret:
            return False
        
        return self.is_pupil_pos_within_threshold
    
    def release(self):
        """Release camera resources"""
        if self.cap:
            self.cap.release()

    #Prompts the user to select a video file if the hardcoded path is not found
    #This is just for my debugging convenience :)
    def select_video(self):
        root = tk.Tk()
        root.withdraw()  # Hide the main window

        video_path = './assets/eye_test.mp4'
        abs_path = os.path.abspath(video_path)    # Get absolute path

        if not os.path.exists(abs_path):
            print("No file found at hardcoded path. Please select a video file.")
            video_path = filedialog.askopenfilename(title="Select Video File", filetypes=[("Video Files", "*.mp4;*.avi")])
            if not video_path:
                print("No file selected. Exiting.")
                return

        connect_to_arduino = False
        
        if connect_to_arduino:
            # Connect to Arduino
            time.sleep(1.5)
            if self.tracker.arduino is None:
                print("Failed to connect to Arduino, instance not connected")
                return
            
            arduino = self.tracker.arduino
        else:
            arduino = None
                
        # first parameter is for path of video
        # second parameter is 1 for video 2 for webcam
        # third parameter is for zoom_factor
        # fourth parameter is for zoom_center, none == (center,center)
        # fifth parameter is for lock_pos_threshold , old 90
        # six parameter is the arduino port
        # seven parameter is the threshold confidence 
        self.process_video(abs_path, input_method=2, zoom_factor=1, zoom_center=None, arduino_port=arduino, threshold_swtich_confidence_margin=2)
        # process_video(abs_path, input_method=2, zoom_factor=8, zoom_center=None, arduino_port=arduino, threshold_swtich_confidence_margin=2)
        
if __name__ == "__main__":
    tracker = ArduinoTracker()

    ports = tracker.detect_arduino_ports()
    if not ports:
        print(f"No ports available for connection") 
        # Display some error message showing cant find port 
    elif len(ports) > 1:
        print(f"Ports for connections")
        for prt in ports:
            print(f"Port: {prt}") 
        
        # FUNCTION TO ALLOW USER TO SELECT PORT, but for now just port[0]
        selected_port = ports[0]
    else:
        selected_port = ports[0]
        
    eye = EyeTracker(arduino_tracker=tracker)
    eye.select_video()


