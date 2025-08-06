import cv2
import time

def debug_camera_capabilities():
    """Debug camera capabilities and current settings"""
    print("=== Camera Capability Debug ===")
    
    # Try different backends available on macOS
    backends_to_try = [
        (cv2.CAP_AVFOUNDATION, "AVFoundation (macOS native)"),
        (cv2.CAP_ANY, "Default backend"),
    ]
    
    for backend_id, backend_name in backends_to_try:
        print(f"\n--- Testing {backend_name} ---")
        
        try:
            cap = cv2.VideoCapture(0, backend_id)
            if not cap.isOpened():
                print(f"❌ Failed to open with {backend_name}")
                continue
                
            print(f"✅ Successfully opened with {backend_name}")
            
            # Get current settings before any changes
            print("\nCurrent camera settings:")
            properties = [
                (cv2.CAP_PROP_FRAME_WIDTH, "Width"),
                (cv2.CAP_PROP_FRAME_HEIGHT, "Height"),
                (cv2.CAP_PROP_FPS, "FPS"),
                (cv2.CAP_PROP_FOURCC, "FourCC"),
                (cv2.CAP_PROP_BRIGHTNESS, "Brightness"),
                (cv2.CAP_PROP_CONTRAST, "Contrast"),
                (cv2.CAP_PROP_SATURATION, "Saturation"),
                (cv2.CAP_PROP_AUTO_EXPOSURE, "Auto Exposure"),
                (cv2.CAP_PROP_EXPOSURE, "Exposure"),
                (cv2.CAP_PROP_GAIN, "Gain"),
            ]
            
            for prop, name in properties:
                value = cap.get(prop)
                if prop == cv2.CAP_PROP_FOURCC and value > 0:
                    fourcc_str = ''.join([chr(int(value >> (8*i)) & 255) for i in range(4)])
                    print(f"  {name}: {fourcc_str} ({int(value)})")
                else:
                    print(f"  {name}: {value}")
            
            # Test frame capture quality
            print(f"\nTesting frame capture...")
            ret, frame = cap.read()
            if ret:
                print(f"  Frame shape: {frame.shape}")
                print(f"  Frame dtype: {frame.dtype}")
                # Calculate basic quality metrics
                mean_intensity = frame.mean()
                std_intensity = frame.std()
                print(f"  Mean intensity: {mean_intensity:.2f}")
                print(f"  Std deviation: {std_intensity:.2f} (higher = less uniform/potentially more detail)")
            else:
                print("  ❌ Failed to capture frame")
            
            cap.release()
            
        except Exception as e:
            print(f"❌ Error with {backend_name}: {e}")

def test_resolution_fps_combinations():
    """Test different resolution and FPS combinations"""
    print("\n=== Testing Resolution/FPS Combinations ===")
    
    # Common resolution/fps combinations for Logitech Brio
    test_combinations = [
        (4096, 2160, 60),  # 4K30
        (4096, 2160, 30),  # 4K30
        (3840, 2160, 60),  # 4K30
        (3840, 2160, 30),  # 4K30
        (3840, 2160, 24),  # 4K24
        (2560, 1440, 60),  # 1440p30
        (2560, 1440, 30),  # 1440p30
        (2048, 1080, 60),
        (2048, 1080, 30),
        (1920, 1080, 60),  # 1080p60
        (1920, 1080, 30),  # 1080p30
        (1280, 720, 60),   # 720p60
    ]
    
    # Use AVFoundation for macOS
    cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)
    if not cap.isOpened():
        cap = cv2.VideoCapture(0)
    
    for width, height, fps in test_combinations:
        print(f"\nTesting {width}x{height} @ {fps}fps")
        
        # Set resolution
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        cap.set(cv2.CAP_PROP_FPS, fps)
        
        # Wait for settings to take effect
        time.sleep(0.5)
        
        # Check actual values
        actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps = cap.get(cv2.CAP_PROP_FPS)
        
        # Test frame capture
        ret, frame = cap.read()
        if ret:
            actual_frame_shape = frame.shape
            success = (actual_width == width and actual_height == height)
            print(f"  Requested: {width}x{height}@{fps} | Actual: {actual_width}x{actual_height}@{actual_fps:.1f}")
            print(f"  Frame shape: {actual_frame_shape} | Success: {'✅' if success else '❌'}")
        else:
            print(f"  ❌ Failed to capture frame")
    
    cap.release()

def optimized_brio_initialization():
    """Optimized initialization for Logitech Brio on macOS"""
    print("\n=== Optimized Brio Initialization ===")
    
    try:
        # Use AVFoundation backend for macOS (much better than default)
        cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)
        
        if not cap.isOpened():
            print("AVFoundation failed, trying default backend")
            cap = cv2.VideoCapture(0)
            
        if not cap.isOpened():
            print("❌ Failed to open camera")
            return None
            
        print("✅ Camera opened successfully")
        
        # Start with a more conservative resolution/fps combination
        # Brio supports 4K30 or 1080p60, but not 4K60
        width, height, fps = 1920, 1080, 60  # Start with 1080p60
        
        # Set resolution and framerate
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        cap.set(cv2.CAP_PROP_FPS, fps)
        
        # Try different codecs (macOS may prefer different formats)
        codecs_to_try = [
            cv2.VideoWriter_fourcc('M','J','P','G'),  # Motion JPEG (widely supported)
            cv2.VideoWriter_fourcc('Y','U','Y','V'),  # YUYV (uncompressed)
            -1  # Let system choose
        ]
        
        for codec in codecs_to_try:
            if codec != -1:
                cap.set(cv2.CAP_PROP_FOURCC, codec)
            
            # Minimal buffer for low latency
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # Conservative quality settings
            cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)  # Some auto-exposure
            cap.set(cv2.CAP_PROP_BRIGHTNESS, 0.0)      # Let auto-exposure handle this
            cap.set(cv2.CAP_PROP_CONTRAST, 0.0)        # Neutral
            cap.set(cv2.CAP_PROP_SATURATION, 0.0)      # Neutral
            
            # Important: Disable auto white balance if supported
            try:
                cap.set(cv2.CAP_PROP_AUTO_WB, 0)
                cap.set(cv2.CAP_PROP_WB_TEMPERATURE, 5000)
            except:
                pass  # Not all backends support this
                
            # Minimize gain to reduce noise
            cap.set(cv2.CAP_PROP_GAIN, 0)
            
            # Wait for camera to stabilize
            time.sleep(1)
            
            # Test capture
            ret, frame = cap.read()
            if ret:
                actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                actual_fps = cap.get(cv2.CAP_PROP_FPS)
                
                codec_name = "System Default" if codec == -1 else ''.join([chr((codec >> 8*i) & 0xFF) for i in range(4)])
                
                print(f"Codec: {codec_name}")
                print(f"Resolution: {actual_width}x{actual_height} (requested: {width}x{height})")
                print(f"FPS: {actual_fps} (requested: {fps})")
                print(f"Frame shape: {frame.shape}")
                print(f"Frame quality - Mean: {frame.mean():.2f}, Std: {frame.std():.2f}")
                
                if frame.std() > 10:  # Basic quality check
                    print("✅ Frame quality looks good")
                    return cap
                else:
                    print("⚠️ Frame quality seems poor (low variation)")
            
        print("❌ All codec attempts failed")
        cap.release()
        return None
        
    except Exception as e:
        print(f"❌ Error during initialization: {e}")
        return None

if __name__ == "__main__":
    # Run all debugging functions
    debug_camera_capabilities()
    test_resolution_fps_combinations()
    
    # Test optimized initialization
    cap = optimized_brio_initialization()
    if cap:
        print("\n✅ Optimized initialization successful!")
        
        # Capture and save a test image for quality comparison
        ret, frame = cap.read()
        if ret:
            cv2.imwrite('brio_test_opencv.jpg', frame)
            print("Test image saved as 'brio_test_opencv.jpg'")
            print("Compare this with a photo taken in PhotoBooth to see quality difference")
        
        cap.release()
    else:
        print("\n❌ Optimized initialization failed")

    print("\nDebugging complete!")