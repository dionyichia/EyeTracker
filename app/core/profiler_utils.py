import cProfile
import pstats
import time
import cv2
import numpy as np
from functools import wraps
import psutil
import os

class EyeTrackerProfiler:
    """Profiling utilities for the EyeTracker application"""
    
    def __init__(self):
        self.frame_times = []
        self.processing_times = {}
        self.memory_usage = []
        
    @staticmethod
    def profile_method(method_name):
        """Decorator to profile individual methods"""
        def decorator(func):
            @wraps(func)
            def wrapper(self, *args, **kwargs):
                start_time = time.time()
                result = func(self, *args, **kwargs)
                end_time = time.time()
                
                if not hasattr(self, 'profiler_times'):
                    self.profiler_times = {}
                if method_name not in self.profiler_times:
                    self.profiler_times[method_name] = []
                    
                self.profiler_times[method_name].append(end_time - start_time)
                return result
            return wrapper
        return decorator
    
    def profile_full_application(self, eye_tracker_instance, num_frames=100):
        """Profile the complete application for specified number of frames"""
        print(f"Profiling {num_frames} frames...")
        
        # Profile using cProfile
        profiler = cProfile.Profile()
        profiler.enable()
        
        frame_count = 0
        total_start = time.time()
        
        while frame_count < num_frames:
            frame_start = time.time()
            
            # Get and process frame
            processed_frame = eye_tracker_instance.get_processed_frame()
            if processed_frame is None:
                break
                
            frame_end = time.time()
            self.frame_times.append(frame_end - frame_start)
            
            # Track memory usage every 10 frames
            if frame_count % 10 == 0:
                process = psutil.Process(os.getpid())
                self.memory_usage.append(process.memory_info().rss / 1024 / 1024)  # MB
                
            frame_count += 1
            
        total_end = time.time()
        profiler.disable()
        
        # Save profiling results
        profiler.dump_stats('eye_tracker_profile.prof')
        
        # Print summary
        self.print_profiling_summary(total_end - total_start, frame_count)
        
        return profiler
    
    def print_profiling_summary(self, total_time, frame_count):
        """Print profiling summary"""
        print("\n" + "="*50)
        print("PROFILING SUMMARY")
        print("="*50)
        
        if self.frame_times:
            avg_frame_time = np.mean(self.frame_times)
            fps = 1.0 / avg_frame_time if avg_frame_time > 0 else 0
            
            print(f"Total frames processed: {frame_count}")
            print(f"Total time: {total_time:.2f}s")
            print(f"Average FPS: {fps:.2f}")
            print(f"Average frame time: {avg_frame_time*1000:.2f}ms")
            print(f"Min frame time: {min(self.frame_times)*1000:.2f}ms")
            print(f"Max frame time: {max(self.frame_times)*1000:.2f}ms")
            
        if self.memory_usage:
            print(f"Average memory usage: {np.mean(self.memory_usage):.2f}MB")
            print(f"Peak memory usage: {max(self.memory_usage):.2f}MB")
            
        print("\nTop time-consuming functions:")
        stats = pstats.Stats('eye_tracker_profile.prof')
        stats.sort_stats('cumulative').print_stats(10)

class OptimizedEyeTracker:
    """Optimized version of your EyeTracker with performance improvements"""
    
    def __init__(self, original_tracker):
        self.original = original_tracker
        # Pre-allocate arrays to avoid repeated memory allocation
        self.temp_arrays = {}
        self.kernel_cache = {}
        
    def get_cached_kernel(self, size):
        """Cache morphological kernels to avoid recreating them"""
        if size not in self.kernel_cache:
            self.kernel_cache[size] = np.ones((size, size), np.uint8)
        return self.kernel_cache[size]
    
    def optimized_process_frames(self, prev_threshold_index, threshold_switch_confidence_margin,
                               thresholded_images, frame, gray_frame):
        """Optimized version of process_frames method"""
        
        # Pre-allocate variables
        final_rotated_rect = ((0,0),(0,0),0)
        final_contours = []
        goodness = []
        best_image_threshold_index = 1
        final_goodness = 0
        
        # Use cached kernel
        kernel = self.get_cached_kernel(5)
        
        # Process each threshold level
        for i, thresholded_img in enumerate(thresholded_images):
            # Dilate the binary image
            dilated_image = cv2.dilate(thresholded_img, kernel, iterations=2)
            
            # Find contours (this is expensive)
            contours, _ = cv2.findContours(dilated_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filter contours - this is a major bottleneck in your original code
            filtered_contours = self.fast_filter_contours(contours, min_area=1000, max_contours=3)
            
            if filtered_contours and len(filtered_contours[0]) > 5:
                # Calculate goodness metric
                current_goodness = self.calculate_ellipse_goodness(dilated_image, filtered_contours[0])
                
                if current_goodness > final_goodness:
                    best_image_threshold_index = i
                    final_goodness = current_goodness
                    final_contours = filtered_contours
                    
                goodness.append(current_goodness)
            else:
                goodness.append(0)
        
        # Apply confidence-based threshold switching
        if best_image_threshold_index != prev_threshold_index and goodness:
            prev_goodness = goodness[prev_threshold_index] if prev_threshold_index < len(goodness) else 0
            
            if goodness[best_image_threshold_index] > prev_goodness * (1 + threshold_switch_confidence_margin):
                prev_threshold_index = best_image_threshold_index
        
        # Draw results on frame
        processed_frame = self.draw_results(frame, final_contours)
        
        return processed_frame, final_rotated_rect, final_contours, prev_threshold_index
    
    def fast_filter_contours(self, contours, min_area=1000, max_contours=3):
        """Optimized contour filtering"""
        if not contours:
            return []
            
        # Calculate areas once and filter
        contour_areas = [(cv2.contourArea(contour), contour) for contour in contours if cv2.contourArea(contour) > min_area]
        
        if not contour_areas:
            return []
            
        # Sort by area and take largest
        contour_areas.sort(key=lambda x: x[0], reverse=True)
        return [contour_areas[0][1]]  # Return largest contour
    
    def calculate_ellipse_goodness(self, image, contour):
        """Simplified ellipse goodness calculation"""
        try:
            if len(contour) < 5:
                return 0
            
            ellipse = cv2.fitEllipse(contour)
            
            # Simple goodness metric based on contour area vs ellipse area
            contour_area = cv2.contourArea(contour)
            ellipse_area = np.pi * (ellipse[1][0]/2) * (ellipse[1][1]/2)
            
            if ellipse_area == 0:
                return 0
                
            return contour_area / ellipse_area
            
        except:
            return 0
    
    def draw_results(self, frame, contours):
        """Optimized drawing of results"""
        if contours and len(contours[0]) > 5:
            try:
                ellipse = cv2.fitEllipse(contours[0])
                center_x, center_y = map(int, ellipse[0])
                cv2.circle(frame, (center_x, center_y), 3, (255, 255, 0), -1)
                cv2.ellipse(frame, ellipse, (255, 0, 0), 2)
            except:
                pass
                
        return frame

# Performance testing utilities
def benchmark_frame_processing(eye_tracker, num_frames=50):
    """Benchmark frame processing performance"""
    print(f"Benchmarking {num_frames} frames...")
    
    times = []
    for i in range(num_frames):
        start = time.time()
        frame = eye_tracker.get_processed_frame()
        end = time.time()
        
        if frame is not None:
            times.append(end - start)
        
        if i % 10 == 0:
            print(f"Processed {i}/{num_frames} frames")
    
    if times:
        avg_time = np.mean(times)
        fps = 1.0 / avg_time
        print(f"\nBenchmark Results:")
        print(f"Average frame time: {avg_time*1000:.2f}ms")
        print(f"Average FPS: {fps:.2f}")
        print(f"Min time: {min(times)*1000:.2f}ms")
        print(f"Max time: {max(times)*1000:.2f}ms")
        
        return {
            'avg_fps': fps,
            'avg_time_ms': avg_time * 1000,
            'min_time_ms': min(times) * 1000,
            'max_time_ms': max(times) * 1000
        }
    
    return None

def identify_bottlenecks():
    """Print common bottlenecks and solutions"""
    print("\n" + "="*60)
    print("COMMON BOTTLENECKS IN YOUR CODE:")
    print("="*60)
    
    bottlenecks = [
        {
            'issue': 'Multiple Threshold Processing',
            'location': 'process_frames() method',
            'impact': 'HIGH - Processing 3 different thresholds per frame',
            'solution': 'Use adaptive thresholding or reduce to 1-2 levels'
        },
        {
            'issue': 'Repeated Contour Filtering',
            'location': 'filter_contours_by_area_and_return_largest()',
            'impact': 'MEDIUM - Called 3 times per frame',
            'solution': 'Cache results or optimize filtering algorithm'
        },
        {
            'issue': 'Memory Allocation',
            'location': 'Array creation in process_frames()',
            'impact': 'MEDIUM - Creating new arrays each frame',
            'solution': 'Pre-allocate arrays and reuse them'
        },
        {
            'issue': 'OpenCV Window Updates',
            'location': 'cv2.imshow() calls',
            'impact': 'HIGH if enabled - GUI updates are expensive',
            'solution': 'Disable for production or update less frequently'
        },
        {
            'issue': 'Ellipse Fitting',
            'location': 'cv2.fitEllipse() calls',
            'impact': 'MEDIUM - Called multiple times per frame',
            'solution': 'Only fit ellipse for best contour'
        }
    ]
    
    for i, bottleneck in enumerate(bottlenecks, 1):
        print(f"{i}. {bottleneck['issue']}")
        print(f"   Location: {bottleneck['location']}")
        print(f"   Impact: {bottleneck['impact']}")
        print(f"   Solution: {bottleneck['solution']}\n")
