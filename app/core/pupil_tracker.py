import cv2
import numpy as np
import math
import tkinter as tk
import os
from tkinter import filedialog
import matplotlib.pyplot as plt
import time
import gc

from app.core.arduino_tracker import ArduinoTracker
from app.core.pupil_tracker_utils import EyeTrackerUtils
# FOR PROFILLING
"""
# Add your app directory to path (adjust as needed)
sys.path.append('./app/core')  # Adjust this path to your app structure
from arduino_tracker import ArduinoTracker
from pupil_tracker_utils import EyeTrackerUtils
"""

class EyeTracker():
    """Class for tracking eye pupil position using OpenCV"""
    
    # Video input config params, for debugging and demonstration
    CAMERA_FEED = 0
    TEST_VIDEO = 1
    KERNEL_SIZE = 5
    
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
        self.zoom_center = None 
        self.threshold_switch_confidence_margin = 2
        
        # State tracking
        self.pupil_center_pos = None # Tracks the center of the pupil (center of darkest area)
        self.is_position_locked = False # False if not calibrated, i.e. Locked when user's pupil is at the correct position
        self.locked_position = -1 # Tracks the locked position coordinates, the calibrated position.
        self.distance_between_pupilpos_and_lockpos = 0 # Tracks the distance between the pupil pos in the current frame with the initial calibrated position
        self.is_pupil_pos_within_threshold = True # True if the distance between the pupil pos current frame within the set threshold. i.e. False if too far, user is looking away
        self.prev_command = 'L'
        self.frame_count = 0

        self.prev_threshold_index = 0 # Tracks the grayscale threshold used. There are 3 grayscale thresholds used, for differing degree of strictness. 1 - light, 2 - medium, 3 - heavy (strict). The threshold used is dynamically determined to give best fitted pupil.

        # Pre-allocate working arrays, to reduce memory usage
        self.working_arrays = {
            'kernel': np.ones((self.KERNEL_SIZE, self.KERNEL_SIZE), np.uint8),
        }
        
        # Initialize camera
        self._initialize_camera()

    def process_frames(self, prev_threshold_index, threshold_swtich_confidence_margin, 
                    thresholded_image_strict, thresholded_image_medium, thresholded_image_relaxed, 
                    frame, gray_frame
                    ):
        """
        Process frames but don't show OpenCV windows
        """
        kernel = self.working_arrays.get('kernel')
        if kernel is None:
            raise ValueError("Kernel not found in working_arrays.")
        
        image_array = [thresholded_image_relaxed, thresholded_image_medium, thresholded_image_strict] #holds images
        goodness = [0] * 3 # goodness arr for to store goodness for all ellipse
        final_contours = [[] for _ in range (3)] #holds final contours
        ellipse_reduced_contours = [[] for _ in range (3)] #holds an array of the best contour points from the fitting process
        
        final_rotated_rect = ((0,0),(0,0),0)
        final_goodness = 0
        best_image_threshold_index = 1
        
        #iterate through binary images and see which fits the ellipse best
        for i, img in enumerate(image_array):
            # Dilate the binary image
            dilated_image = cv2.dilate(img, kernel, iterations=2)
            
            # Find contours
            contours, _ = cv2.findContours(dilated_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Create an empty image to draw contours
            # contour_img2 = np.zeros_like(dilated_image)
            reduced_contours = EyeTrackerUtils.filter_contours_by_area_and_return_largest(contours, 1000, 3)

            if reduced_contours and len(reduced_contours[0]) > 5:
                # Cache the main contour for reuse
                main_contour = reduced_contours[0]

                # Calculate goodness and pixel metrics
                current_goodness = EyeTrackerUtils.check_ellipse_goodness(dilated_image, main_contour)
                total_pixels = EyeTrackerUtils.check_contour_pixels(main_contour, dilated_image.shape) #  in total pixels, first element is pixel total, next is ratio 
                
                # Combined goodness score
                current_score = current_goodness[0]*total_pixels[0]*total_pixels[0]*total_pixels[1]
            
                goodness[i] = current_score
                ellipse_reduced_contours[i] = total_pixels[2]
                final_contours[i] = reduced_contours

                # If the current iteration has the best goodness set it as best_image_threshold_index
                if current_score > final_goodness:
                    best_image_threshold_index = i-1
                    final_goodness = current_score
            
        # Confidence-Based Threshold Switching, to prevent flickering caused by toggling between thresholds, only switch if goodness difference btw thres is significant
        # If the threshold index used in the previous frame and cur frame are not the same, apply confidence check
        if best_image_threshold_index != prev_threshold_index:
            # Assign the current goodness of prev_threshold_index to prev_goodness
            prev_goodness = goodness[prev_threshold_index] if 0 <= prev_threshold_index < 3 else 0
        
            # If the best_image index's goodness is better than prev_goodness by the stipluted margin, switch images, else dont 
            if goodness[best_image_threshold_index] > prev_goodness * (1 + threshold_swtich_confidence_margin):
                print("Changed prev_threshold_index ", prev_threshold_index, " prev_goodness ", prev_goodness, " cur index ", best_image_threshold_index, " goodness ", goodness[best_image_threshold_index])
                prev_threshold_index = best_image_threshold_index

        # Use the selected threshold results
        selected_contours = final_contours[prev_threshold_index]

        # If user has selected lockpos, i.e. calibrated
        if self.is_position_locked:
            # print("lock_mode_on running,  track_darkest_pt ", self.locked_position,  " darkest_point ", self.pupil_center_pos)
            if self.locked_position == -1:
                print("Calibration Error:, pupil position not calibrated!")
            else:
                # Calc euclid dist between curr darkest point and calibrated position
                self.distance_between_pupilpos_and_lockpos =  math.dist(self.locked_position, self.pupil_center_pos) 
                frame = self.lockpos(frame, selected_contours)

        test_frame = frame.copy()
        
        if selected_contours:
            optimised_contours = [EyeTrackerUtils.optimize_contours_by_angle(selected_contours, gray_frame)]
            
            if optimised_contours and not isinstance(optimised_contours[0], list) and len(optimised_contours[0]) > 5:
                ellipse = cv2.fitEllipse(optimised_contours[0])
                final_rotated_rect = ellipse
                center_x, center_y = map(int, ellipse[0])
                cv2.circle(test_frame, (center_x, center_y), 3, (255, 255, 0), -1)

                if self.is_position_locked == False:
                    cv2.ellipse(test_frame, ellipse, (255, 0, 0), 2)

        else:
            optimised_contours = []

        del frame, dilated_image, contours, reduced_contours, final_contours 

        # Return the test_frame which has all the visualizations
        return test_frame, final_rotated_rect, optimised_contours, prev_threshold_index

    # Finds the pupil in an individual frame and returns the center point
    def _process_single_frame(self, frame):
        """Process a single frame with all your existing algorithms"""
        if frame is None:
            return None
            
        # Crop and resize frame
        frame = EyeTrackerUtils.crop_to_aspect_ratio(frame)
        
        # Apply zoom effect if needed
        if self.zoom_factor > 1:
            frame = EyeTrackerUtils.zoom_frame(frame, self.zoom_factor, self.zoom_center)
        
        # Find the darkest point (pupil center)
        self.pupil_center_pos = EyeTrackerUtils.get_darkest_area_optimised(frame)
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
        
        del frame, gray_frame, thresholded_image_strict, thresholded_image_medium, thresholded_image_relaxed
        
        # Return the processed frame with visualizations
        return processed_frame

    def get_processed_frame(self):
        """Get current frame with processing applied - called by GUI timer"""
        if not self.cap or not self.cap.isOpened():
            return None
        
        ret, frame = self.cap.read()
        if not ret:
            return None
        
        self.frame_count += 1
        
        # Apply all processing steps and return the processed frame
        processed_frame = self._process_single_frame(frame)

        if self.frame_count % 10 == 0:
            print("gc force trash collecting")
            self.cleanup_frame_data()

        return processed_frame

    def _initialize_camera(self):
        """Initialize the webcam"""
        try:
            if self.vid_input:
                self.cap = cv2.VideoCapture(0)  # Use default camera // NOT FIXED need to think of some realtive path maybe idk
            else:
                self.cap = cv2.VideoCapture(0)  # Use default camera

            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 2048)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
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
            command = 'H'

            
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
            command = 'L'
            
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

    def set_zoom(self, value, center=None):
        """
        Set the zoom factor and zoom center for the video feed
        
        :param value: Zoom factor (1 = no zoom)
        :param center: Optional tuple (x, y) with coordinates in range 0-1 for the zoom center
        """
        self.zoom_factor = value
        self.zoom_center = center 
    
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
            frame = EyeTrackerUtils.zoom_frame(frame, self.zoom_factor, self.zoom_center)
            
        self.locked_position = EyeTrackerUtils.get_darkest_area_optimised(frame)
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
        
        # ret, frame = self.cap.read()
        # if not ret:
        #     return False
        
        return self.is_pupil_pos_within_threshold
    
    # Add to your frame processing loop
    def cleanup_frame_data(self):
        """Clean up temporary arrays and matrices"""
        if hasattr(self, '_temp_arrays'):
            for arr in self._temp_arrays:
                if arr is not None:
                    del arr

        gc.collect()  # Force garbage collection
        self.frame_count = 0
    
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


