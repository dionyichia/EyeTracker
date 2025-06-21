#!/usr/bin/env python3
"""
Simple profiler for EyeTracker class
Usage: python profiler_main.py
"""

import sys
import os
import time
import cProfile
import pstats
import psutil
import numpy as np

# Add your app directory to path (adjust as needed)
# sys.path.append('./app/core')  # Adjust this path to your app structure

from app.core.pupil_tracker import EyeTracker 
# from app.core.arduino_tracker import ArduinoTracker

def profile_eye_tracker(num_frames=50):
    """Profile EyeTracker performance"""
    print(f"Starting EyeTracker profiling with {num_frames} frames...")
    
    # Initialize EyeTracker (without Arduino for testing)
    eye_tracker = EyeTracker(arduino_tracker=None)
    
    if not eye_tracker.cap or not eye_tracker.cap.isOpened():
        print("ERROR: Could not initialize camera")
        return
    
    # Warm up (first few frames are often slower)
    print("Warming up...")
    for _ in range(5):
        eye_tracker.get_processed_frame()
    
    # Start profiling
    print("Starting profiling...")
    profiler = cProfile.Profile()
    
    frame_times = []
    memory_usage = []
    
    profiler.enable()
    
    for i in range(num_frames):
        # Track memory every 10 frames
        if i % 10 == 0:
            process = psutil.Process(os.getpid())
            memory_usage.append(process.memory_info().rss / 1024 / 1024)  # MB
            print(f"Frame {i}/{num_frames} - Memory: {memory_usage[-1]:.1f}MB")
        
        # Time individual frame processing
        start_time = time.time()
        processed_frame = eye_tracker.get_processed_frame()
        frame_time = time.time() - start_time
        
        if processed_frame is not None:
            frame_times.append(frame_time)
        else:
            print(f"Warning: Frame {i} returned None")
            break
    
    profiler.disable()
    
    # Save profiling data
    profiler.dump_stats('eye_tracker_profile.prof')
    
    # Print results
    print_results(frame_times, memory_usage, len(frame_times))
    
    # Print top time-consuming functions
    print("\n" + "="*60)
    print("TOP TIME-CONSUMING FUNCTIONS:")
    print("="*60)
    stats = pstats.Stats('eye_tracker_profile.prof')
    stats.sort_stats('cumulative')
    stats.print_stats(15)  # Show top 15 functions
    
    eye_tracker.release()
    return stats

def print_results(frame_times, memory_usage, frame_count):
    """Print profiling results"""
    print("\n" + "="*50)
    print("PROFILING RESULTS")
    print("="*50)
    
    if frame_times:
        avg_time = np.mean(frame_times)
        fps = 1.0 / avg_time if avg_time > 0 else 0
        
        print(f"Frames processed: {frame_count}")
        print(f"Average FPS: {fps:.2f}")
        print(f"Average frame time: {avg_time*1000:.2f}ms")
        print(f"Min frame time: {min(frame_times)*1000:.2f}ms")
        print(f"Max frame time: {max(frame_times)*1000:.2f}ms")
        print(f"Frame time std dev: {np.std(frame_times)*1000:.2f}ms")
        
        # Performance categories
        if fps >= 50:
            print("✅ PERFECT: Real-time performance (50+ FPS)")
        elif fps >= 30:
            print("✅ EXCELLENT: Real-time performance (30-50 FPS)")
        elif fps >= 15:
            print("⚠️  GOOD: Acceptable performance (15-30 FPS)")
        elif fps >= 5:
            print("⚠️  SLOW: Poor performance (5-15 FPS)")
        else:
            print("❌ CRITICAL: Very poor performance (<5 FPS)")
    
    if memory_usage:
        print(f"\nMemory usage:")
        print(f"Average: {np.mean(memory_usage):.1f}MB")
        print(f"Peak: {max(memory_usage):.1f}MB")
        print(f"Memory growth: {memory_usage[-1] - memory_usage[0]:.1f}MB")

def quick_benchmark():
    """Quick performance check"""
    print("Quick benchmark test...")
    
    eye_tracker = EyeTracker(arduino_tracker=None)
    
    if not eye_tracker.cap or not eye_tracker.cap.isOpened():
        print("ERROR: Could not initialize camera")
        return
    
    # Test 10 frames
    times = []
    for i in range(10):
        start = time.time()
        frame = eye_tracker.get_processed_frame()
        end = time.time()
        
        if frame is not None:
            times.append(end - start)
            print(f"Frame {i+1}: {(end-start)*1000:.1f}ms")
    
    if times:
        avg_fps = 1.0 / np.mean(times)
        print(f"\nQuick test average: {avg_fps:.1f} FPS")
    
    eye_tracker.release()

if __name__ == "__main__":
    print("EyeTracker Profiler")
    print("==================")
    
    # Check if camera is available
    import cv2
    test_cap = cv2.VideoCapture(0)
    if not test_cap.isOpened():
        print("ERROR: No camera detected")
        sys.exit(1)
    test_cap.release()
    
    try:
        # Run quick benchmark first
        quick_benchmark()
        
        print("\n" + "-"*50)
        
        # Run full profiling
        profile_eye_tracker(num_frames=50)
        
        print("\n" + "="*50)
        print("PROFILING COMPLETE")
        print("="*50)
        print("Profile data saved to: eye_tracker_profile.prof")
        print("\nTo view detailed profile:")
        print("python -c \"import pstats; pstats.Stats('eye_tracker_profile.prof').sort_stats('cumulative').print_stats(20)\"")
        
    except KeyboardInterrupt:
        print("\nProfiling interrupted by user")
    except Exception as e:
        print(f"Error during profiling: {e}")
        import traceback
        traceback.print_exc()