import cv2
import numpy as np

class EyeTrackerUtils:
    # Image Processing Functions

    # Crop the image to maintain a specific aspect ratio (width:height) before resizing. 
    @staticmethod
    def crop_to_aspect_ratio(image, width=640, height=480):
        
        # Calculate current aspect ratio
        current_height, current_width = image.shape[:2]
        desired_ratio = width / height
        current_ratio = current_width / current_height

        if current_ratio > desired_ratio:
            # Current image is too wide
            new_width = int(desired_ratio * current_height)
            offset = (current_width - new_width) // 2
            cropped_img = image[:, offset:offset+new_width]
        else:
            # Current image is too tall
            new_height = int(current_width / desired_ratio)
            offset = (current_height - new_height) // 2
            cropped_img = image[offset:offset+new_height, :]

        return cv2.resize(cropped_img, (width, height))
    
    # Apply thresholding to an image
    @staticmethod
    def apply_binary_threshold(image, darkestPixelValue, addedThreshold):
        # Calculate the threshold as the sum of the two input values
        threshold = darkestPixelValue + addedThreshold
        # Apply the binary threshold
        _, thresholded_image = cv2.threshold(image, threshold, 255, cv2.THRESH_BINARY_INV)
        
        return thresholded_image
    
    @staticmethod
    def zoom_frame(frame, zoom_factor, center=None):
        """
        Zooms into a specific area of the frame based on the zoom factor.
        
        :param frame: The input frame (image) to zoom into.
        :param zoom_factor: The factor by which to zoom. Values greater than 1 will zoom in.
        :param center: The center of the zoom as a tuple of (x_ratio, y_ratio) in the range 0-1.
                    If None, zooms into the center of the frame.
        :return: The zoomed-in frame.
        """
        (h, w) = frame.shape[:2]
        
        # Get center coordinates
        if center is None:
            center_x = w // 2
            center_y = h // 2
        else:
            # Convert from ratio (0-1) to pixel coordinates
            center_x = int(w * center[0])
            center_y = int(h * center[1])
        
        # Calculate the new dimensions
        new_w = int(w / zoom_factor)
        new_h = int(h / zoom_factor)
        
        # Calculate the cropping box
        x = max(center_x - new_w // 2, 0)
        y = max(center_y - new_h // 2, 0)
        
        # Ensure we're not exceeding frame bounds
        if x + new_w > w:
            x = w - new_w
        if y + new_h > h:
            y = h - new_h
        
        # Ensure cropping box dimensions are valid
        x = max(0, x)
        y = max(0, y)
        x2 = min(x + new_w, w)
        y2 = min(y + new_h, h)
        
        # Crop and resize the frame
        cropped_frame = frame[y:y2, x:x2]
        
        # Check if we have valid dimensions before resizing
        if cropped_frame.shape[0] > 0 and cropped_frame.shape[1] > 0:
            zoomed_frame = cv2.resize(cropped_frame, (w, h))
            return zoomed_frame
        else:
            # Return original frame if cropping resulted in an invalid size
            return frame

    # Contour Detection and Processing
    #mask all pixels outside a square defined by center and size
    @staticmethod
    def mask_outside_square(image, center, size):
        x, y = center
        half_size = size // 2

        # Create a mask initialized to black
        mask = np.zeros_like(image)

        # Calculate the top-left corner of the square
        top_left_x = max(0, x - half_size)
        top_left_y = max(0, y - half_size)

        # Calculate the bottom-right corner of the square
        bottom_right_x = min(image.shape[1], x + half_size)
        bottom_right_y = min(image.shape[0], y + half_size)

        # Set the square area in the mask to white
        mask[top_left_y:bottom_right_y, top_left_x:bottom_right_x] = 255

        # Apply the mask to the image
        masked_image = cv2.bitwise_and(image, mask)

        return masked_image
    
    @staticmethod
    def optimize_contours_by_angle(contours, image):
        if len(contours) < 1:
            return contours

        # Holds the candidate points
        all_contours = np.concatenate(contours[0], axis=0)

        # Set spacing based on size of contours
        spacing = int(len(all_contours)/25)  # Spacing between sampled points

        # Temporary array for result
        filtered_points = []
        
        # Calculate centroid of the original contours
        centroid = np.mean(all_contours, axis=0)
        
        # # Create an image of the same size as the original image
        # point_image = image.copy()
        
        # skip = 0
        
        # Loop through each point in the all_contours array
        for i in range(0, len(all_contours), 1):
        
            # Get three points: current point, previous point, and next point
            current_point = all_contours[i]
            prev_point = all_contours[i - spacing] if i - spacing >= 0 else all_contours[-spacing]
            next_point = all_contours[i + spacing] if i + spacing < len(all_contours) else all_contours[spacing]
            
            # Calculate vectors between points
            vec1 = prev_point - current_point
            vec2 = next_point - current_point
            
            with np.errstate(invalid='ignore'):
                # Calculate angles between vectors
                angle = np.arccos(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))

            # Calculate vector from current point to centroid
            vec_to_centroid = centroid - current_point
            
            # Check if angle is oriented towards centroid
            # Calculate the cosine of the desired angle threshold (e.g., 80 degrees)
            cos_threshold = np.cos(np.radians(60))  # Convert angle to radians
            
            if np.dot(vec_to_centroid, (vec1+vec2)/2) >= cos_threshold:
                filtered_points.append(current_point)
        
        return np.array(filtered_points, dtype=np.int32).reshape((-1, 1, 2))
    
    def optimize_contours_by_angle_vectorised(contours, image):
        """Optimized version with vectorized numpy operations and reduced redundancy"""
        if len(contours) < 1:
            return contours

        # Get all contour points
        all_contours = np.concatenate(contours[0], axis=0)
        n_points = len(all_contours)
        
        if n_points < 3:
            return all_contours.reshape((-1, 1, 2))
        
        # Set spacing based on size of contours (but limit the range)
        spacing = max(1, min(n_points // 25, n_points // 3))
        
        # Pre-calculate centroid once
        centroid = np.mean(all_contours, axis=0)
        
        # Pre-calculate cosine threshold
        cos_threshold = np.cos(np.radians(60))
        
        # Vectorized approach for better performance
        filtered_indices = []
        
        # Process points in batches to reduce memory usage
        batch_size = min(1000, n_points)
        
        for batch_start in range(0, n_points, batch_size):
            batch_end = min(batch_start + batch_size, n_points)
            batch_indices = np.arange(batch_start, batch_end)
            
            # Get current points for this batch
            current_points = all_contours[batch_indices]
            
            # Calculate previous and next indices with wrapping
            prev_indices = (batch_indices - spacing) % n_points
            next_indices = (batch_indices + spacing) % n_points
            
            # Get previous and next points
            prev_points = all_contours[prev_indices]
            next_points = all_contours[next_indices]
            
            # Calculate vectors (vectorized)
            vec1 = prev_points - current_points
            vec2 = next_points - current_points
            
            # Calculate norms once and reuse
            norm1 = np.linalg.norm(vec1, axis=1)
            norm2 = np.linalg.norm(vec2, axis=1)
            
            # Avoid division by zero
            valid_norms = (norm1 > 1e-8) & (norm2 > 1e-8)
            
            if np.any(valid_norms):
                # Calculate dot products (vectorized)
                dot_products = np.sum(vec1 * vec2, axis=1)
                
                # Calculate angles only for valid points
                valid_mask = valid_norms
                angles = np.full(len(batch_indices), np.pi)  # Default to pi for invalid points
                
                with np.errstate(invalid='ignore', divide='ignore'):
                    cos_angles = dot_products[valid_mask] / (norm1[valid_mask] * norm2[valid_mask])
                    # Clamp to valid range for arccos
                    cos_angles = np.clip(cos_angles, -1.0, 1.0)
                    angles[valid_mask] = np.arccos(cos_angles)
                
                # Calculate vectors to centroid (vectorized)
                vec_to_centroid = centroid - current_points
                
                # Calculate average direction vectors
                avg_directions = (vec1 + vec2) / 2
                
                # Calculate dot products with centroid direction (vectorized)
                centroid_dots = np.sum(vec_to_centroid * avg_directions, axis=1)
                
                # Apply filtering criteria
                angle_filter = angles < np.radians(180)  # Reasonable angle threshold
                centroid_filter = centroid_dots >= cos_threshold
                
                # Combine filters
                final_filter = valid_mask & angle_filter & centroid_filter
                
                # Add valid indices to result
                valid_batch_indices = batch_indices[final_filter]
                filtered_indices.extend(valid_batch_indices)
        
        # Return filtered points
        if filtered_indices:
            filtered_points = all_contours[filtered_indices]
            return filtered_points.reshape((-1, 1, 2))
        else:
            # Fallback: return evenly spaced points if no points pass the filter
            step = max(1, n_points // 20)
            fallback_points = all_contours[::step]
            return fallback_points.reshape((-1, 1, 2))

    #returns the largest contour that is not extremely long or tall
    #contours is the list of contours, pixel_thresh is the max pixels to filter, and ratio_thresh is the max ratio
    @staticmethod
    def filter_contours_by_area_and_return_largest(contours, pixel_thresh, ratio_thresh):
        max_area = 0
        largest_contour = None
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area >= pixel_thresh:
                x, y, w, h = cv2.boundingRect(contour)
                length = max(w, h)
                width = min(w, h)

                # Calculate the length-to-width ratio and width-to-length ratio
                length_to_width_ratio = length / width
                width_to_length_ratio = width / length

                # Pick the higher of the two ratios
                current_ratio = max(length_to_width_ratio, width_to_length_ratio)

                # Check if highest ratio is within the acceptable threshold
                if current_ratio <= ratio_thresh:
                    # Update the largest contour if the current one is bigger
                    if area > max_area:
                        max_area = area
                        largest_contour = contour

        # Return a list with only the largest contour, or an empty list if no contour was found
        if largest_contour is not None:
            return [largest_contour]
        else:
            return []

    #Fits an ellipse to the optimized contours and draws it on the image.
    @staticmethod
    def fit_and_draw_ellipses(image, optimized_contours, color):
        if len(optimized_contours) >= 5:
            # Ensure the data is in the correct shape (n, 1, 2) for cv2.fitEllipse
            contour = np.array(optimized_contours, dtype=np.int32).reshape((-1, 1, 2))

            # Fit ellipse
            ellipse = cv2.fitEllipse(contour)

            # Draw the ellipse
            cv2.ellipse(image, ellipse, color, 2)  # Draw with green color and thickness of 2

            return image
        else:
            print("Not enough points to fit an ellipse.")
            return image

    #checks how many pixels in the contour fall under a slightly thickened ellipse
    #also returns that number of pixels divided by the total pixels on the contour border
    #assists with checking ellipse goodness    
    @staticmethod
    def check_contour_pixels(contour, image_shape):
        # Check if the contour can be used to fit an ellipse (requires at least 5 points)
        if len(contour) < 5:
            return [0, 0]  # Not enough points to fit an ellipse
        
        # Create an empty mask for the contour
        contour_mask = np.zeros(image_shape, dtype=np.uint8)
        # Draw the contour on the mask, filling it
        cv2.drawContours(contour_mask, [contour], -1, (255), 1)
    
        # Fit an ellipse to the contour and create a mask for the ellipse
        ellipse_mask_thick = np.zeros(image_shape, dtype=np.uint8)
        ellipse_mask_thin = np.zeros(image_shape, dtype=np.uint8)
        ellipse = cv2.fitEllipse(contour)
        
        # Draw the ellipse with a specific thickness
        cv2.ellipse(ellipse_mask_thick, ellipse, (255), 10) #capture more for absolute
        cv2.ellipse(ellipse_mask_thin, ellipse, (255), 4) #capture fewer for ratio

        # Calculate the overlap of the contour mask and the thickened ellipse mask
        overlap_thick = cv2.bitwise_and(contour_mask, ellipse_mask_thick)
        overlap_thin = cv2.bitwise_and(contour_mask, ellipse_mask_thin)
        
        # Count the number of non-zero (white) pixels in the overlap
        absolute_pixel_total_thick = np.sum(overlap_thick > 0)#compute with thicker border
        absolute_pixel_total_thin = np.sum(overlap_thin > 0)#compute with thicker border
        
        # Compute the ratio of pixels under the ellipse to the total pixels on the contour border
        total_border_pixels = np.sum(contour_mask > 0)
        
        ratio_under_ellipse = absolute_pixel_total_thin / total_border_pixels if total_border_pixels > 0 else 0
        
        return [absolute_pixel_total_thick, ratio_under_ellipse, overlap_thin]

    
    #Finds a square area of dark pixels in the image, original brute force method, just left here for reference
    #@param I input image (converted to grayscale during search process)
    #@return a point within the pupil region
    @staticmethod
    def get_darkest_area(image):
        if image is None:
            print("Error: Image not loaded properly")
            return None

        ignoreBounds = 20
        imageSkipSize = 10
        searchArea = 20
        internalSkipSize = 5
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        min_sum = float('inf')
        darkest_point = None

        # Loop over the image with spacing defined by imageSkipSize, ignoring the boundaries
        for y in range(ignoreBounds, gray.shape[0] - ignoreBounds - searchArea, imageSkipSize):
            for x in range(ignoreBounds, gray.shape[1] - ignoreBounds - searchArea, imageSkipSize):

                current_sum = 0
                num_pixels = 0
                for dy in range(0, searchArea, internalSkipSize):
                    if (y + dy) >= gray.shape[0]:
                        break
                    for dx in range(0, searchArea, internalSkipSize):
                        if (x + dx) >= gray.shape[1]:
                            break

                        current_sum = current_sum + gray[y + dy,x + dx].astype(np.int32)
                        num_pixels += 1

                # Update the darkest point if the current block is darker
                if current_sum < min_sum and num_pixels > 0:
                    min_sum = current_sum
                    darkest_point = (x + searchArea // 2, y + searchArea // 2)  # Center of the block
                
        return darkest_point
    
    #Finds a square area of dark pixels in the image, uses blur to average darkness of kernel rather than brute force calc
    #@param I input image (converted to grayscale during search process)
    #@return a point within the pupil region    
    @staticmethod
    def get_darkest_area_optimised(image):
        if image is None:
            print("Error: Image not loaded properly")
            return None

        ignoreBounds = 20
        searchArea = 20
        imageSkipSize = 10

        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Crop the image to ignore bounds
        cropped = gray[ignoreBounds:-ignoreBounds, ignoreBounds:-ignoreBounds]

        # Use box filter to compute average pixel values in blocks
        blurred = cv2.blur(cropped, (searchArea, searchArea))  # or cv2.boxFilter with normalize=True

        # Downsample the blurred image to simulate skipping
        downsampled = blurred[::imageSkipSize, ::imageSkipSize]

        # Find the location of the minimum average value (darkest)
        min_loc = np.unravel_index(np.argmin(downsampled), downsampled.shape)

        # Map back to original coordinates
        y_min, x_min = min_loc
        x_orig = ignoreBounds + x_min * imageSkipSize + searchArea // 2
        y_orig = ignoreBounds + y_min * imageSkipSize + searchArea // 2

        return (x_orig, y_orig)

    #Finds a square area of dark pixels in the image, uses np calc and vectors for speed, same output as brute force
    #@param I input image (converted to grayscale during search process)
    #@return a point within the pupil region    
    @staticmethod 
    def get_darkest_area_vectorized(image):
        if image is None:
            print("Error: Image not loaded properly")
            return None

        ignoreBounds = 20
        imageSkipSize = 10
        searchArea = 20
        internalSkipSize = 5
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(np.int32)
        
        # Calculate dimensions
        h, w = gray.shape
        valid_h = h - 2 * ignoreBounds - searchArea
        valid_w = w - 2 * ignoreBounds - searchArea
        
        # Number of positions to check
        num_y = len(range(0, valid_h, imageSkipSize))
        num_x = len(range(0, valid_w, imageSkipSize))
        
        # Pre-allocate results array
        sums = np.full((num_y, num_x), float('inf'))
        
        # Calculate all sums
        for i, y_offset in enumerate(range(0, valid_h, imageSkipSize)):
            for j, x_offset in enumerate(range(0, valid_w, imageSkipSize)):
                y = ignoreBounds + y_offset
                x = ignoreBounds + x_offset
                
                # Extract and sample block
                block = gray[y:y+searchArea:internalSkipSize, x:x+searchArea:internalSkipSize]
                sums[i, j] = np.sum(block)
        
        # Find minimum
        min_idx = np.unravel_index(np.argmin(sums), sums.shape)
        min_i, min_j = min_idx
        
        # Convert back to original coordinates
        y_orig = ignoreBounds + min_i * imageSkipSize + searchArea // 2
        x_orig = ignoreBounds + min_j * imageSkipSize + searchArea // 2
        
        return (x_orig, y_orig)
    
    #outside of this method, select the ellipse with the highest percentage of pixels under the ellipse 
    #TODO for efficiency, work with downscaled or cropped images
    @staticmethod
    def check_ellipse_goodness(binary_image, contour):
        ellipse_goodness = [0,0,0] #covered pixels, edge straightness stdev, skewedness   
        # Check if the contour can be used to fit an ellipse (requires at least 5 points)
        if len(contour) < 5:
            print("length of contour was 0")
            return 0  # Not enough points to fit an ellipse
        
        # Fit an ellipse to the contour
        ellipse = cv2.fitEllipse(contour)
        
        # Create a mask with the same dimensions as the binary image, initialized to zero (black)
        mask = np.zeros_like(binary_image)
        
        # Draw the ellipse on the mask with white color (255)
        cv2.ellipse(mask, ellipse, (255), -1)
        
        # Calculate the number of pixels within the ellipse
        ellipse_area = np.sum(mask == 255)
        
        # Calculate the number of white pixels within the ellipse
        covered_pixels = np.sum((binary_image == 255) & (mask == 255))
        
        # Calculate the percentage of covered white pixels within the ellipse
        if ellipse_area == 0:
            print("area was 0")
            return ellipse_goodness  # Avoid division by zero if the ellipse area is somehow zero
        
        #percentage of covered pixels to number of pixels under area
        ellipse_goodness[0] = covered_pixels / ellipse_area
        
        #skew of the ellipse (less skewed is better?) - may not need this
        # axes_lengths = ellipse[1]  # This is a tuple (minor_axis_length, major_axis_length)
        # major_axis_length = axes_lengths[1]
        # minor_axis_length = axes_lengths[0]
        ellipse_goodness[2] = min(ellipse[1][1]/ellipse[1][0], ellipse[1][0]/ellipse[1][1])
        
        return ellipse_goodness
