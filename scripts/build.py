import subprocess
import os
import shutil
import platform
import sys
import zipfile
import tarfile

def clean_build():
    """Clean previous build artifacts"""
    dirs_to_clean = ['build', 'dist', '__pycache__', 'release']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"Cleaning {dir_name}...")
            shutil.rmtree(dir_name)
    
    # Clean .pyc files recursively
    print("Cleaning .pyc files...")
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.pyc'):
                os.remove(os.path.join(root, file))
    
    # Clean any existing zip/tar.gz files
    for ext in ['*.zip', '*.tar.gz']:
        for file in os.listdir('.'):
            if file.endswith(ext.replace('*', '')):
                print(f"Removing {file}...")
                os.remove(file)

def analyze_build_size():
    """Analyze the build size and show largest components"""
    system = platform.system().lower()
    
    if system == 'darwin':  # macOS
        app_path = 'dist/EyeTracker.app'
        if os.path.exists(app_path):
            # Get total size
            result = subprocess.run(['du', '-sh', app_path], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"\nTotal app size: {result.stdout.strip()}")
            
            # Show largest files in the app bundle
            print("\nLargest files in the app bundle:")
            try:
                result = subprocess.run([
                    'find', app_path, '-type', 'f', '-exec', 'ls', '-lh', '{}', '+', '|',
                    'sort', '-k5', '-hr', '|', 'head', '-20'
                ], shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    print(result.stdout)
            except Exception as e:
                print(f"Could not analyze file sizes: {e}")
            
            # Show framework sizes
            frameworks_path = os.path.join(app_path, 'Contents', 'Frameworks')
            if os.path.exists(frameworks_path):
                print("\nFramework sizes:")
                result = subprocess.run(['du', '-sh', frameworks_path + '/*'], 
                                      shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    print(result.stdout)
    
    elif system in ['windows', 'linux']:
        if system == 'windows':
            exe_name = 'EyeTracker-Windows.exe'
        else:
            exe_name = 'EyeTracker-Linux'
        
        exe_path = f'dist/{exe_name}'
        if os.path.exists(exe_path):
            size = os.path.getsize(exe_path)
            print(f"\nExecutable size: {size / (1024*1024):.1f} MB")

def build_app():
    """Build the application using PyInstaller matching GitHub Actions"""
    system = platform.system().lower()
    
    if system == 'darwin':  # macOS - use spec file from project root
        spec_file = 'build_spec_files/macos/EyeTracker-macOS.spec'
        if not os.path.exists(spec_file):
            raise FileNotFoundError(f"Spec file not found: {spec_file}")
        
        # Run from project root directory to avoid path issues
        cmd = ['pyinstaller', '--clean', spec_file]
        print(f"Building for macOS using spec file: {spec_file}")
        print(f"Working directory: {os.getcwd()}")
        
    elif system == 'windows':  # Windows - direct command
        cmd = [
            'pyinstaller',
            '--noconfirm',
            '--onefile',
            '--windowed',
            '--name=EyeTracker-Windows',
            '--add-data=assets;assets',
            '--add-data=arduino;arduino',
            'main.py'
        ]
        print("Building for Windows using direct PyInstaller command")
        
    elif system == 'linux':  # Linux - direct command
        cmd = [
            'pyinstaller',
            '--noconfirm',
            '--onefile',
            '--windowed',
            '--name=EyeTracker-Linux',
            '--add-data=assets:assets',
            '--add-data=arduino:arduino',
            'main.py'
        ]
        print("Building for Linux using direct PyInstaller command")
    
    else:
        raise ValueError(f"Unsupported platform: {system}")
    
    print(f"Running command: {' '.join(cmd)}")
    
    # Set environment variables for macOS to help with library paths
    env = os.environ.copy()
    if system == 'darwin':
        env['DYLD_LIBRARY_PATH'] = '/opt/homebrew/lib:/usr/local/lib'
        env['PKG_CONFIG_PATH'] = '/opt/homebrew/lib/pkgconfig:/usr/local/lib/pkgconfig'
    
    result = subprocess.run(cmd, env=env, check=True)
    
    if result.returncode == 0:
        print("Build completed successfully!")
        analyze_build_size()
    else:
        print("Build failed!")
        sys.exit(1)

def create_distribution_package():
    """Create distribution package matching GitHub Actions"""
    system = platform.system().lower()
    
    # Create release directory
    os.makedirs('release', exist_ok=True)
    
    if system == 'windows':
        # Windows distribution
        print("Creating Windows distribution package...")
        
        # Copy executable
        shutil.copy('dist/EyeTracker-Windows.exe', 'release/')
        
        # Copy arduino directory
        if os.path.exists('arduino'):
            shutil.copytree('arduino', 'release/arduino')
        
        # Copy documentation
        for file in ['README.md', 'LICENSE']:
            if os.path.exists(file):
                shutil.copy(file, 'release/')
        
        # Create zip file
        print("Creating EyeTracker-Windows.zip...")
        with zipfile.ZipFile('EyeTracker-Windows.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk('release'):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, 'release')
                    zipf.write(file_path, arcname)
        
        print(f"Created EyeTracker-Windows.zip ({os.path.getsize('EyeTracker-Windows.zip') / (1024*1024):.1f} MB)")
        
    elif system == 'darwin':  # macOS
        print("Creating macOS distribution package...")
        
        # Copy app bundle
        if os.path.exists('dist/EyeTracker.app'):
                    subprocess.run([
            'rsync', '-a', '--delete',
            'dist/EyeTracker.app/',  # trailing slash is key
            'release/EyeTracker.app/'
        ], check=True)
        
        # Copy arduino directory
        if os.path.exists('arduino'):
            shutil.copytree('arduino', 'release/arduino')
        
        # Copy documentation
        for file in ['README.md', 'LICENSE']:
            if os.path.exists(file):
                shutil.copy(file, 'release/')
        
        # Create zip file
        print("Creating EyeTracker-macOS.zip...")
        with zipfile.ZipFile('EyeTracker-macOS.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk('release'):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, 'release')
                    zipf.write(file_path, arcname)
        
        print(f"Created EyeTracker-macOS.zip ({os.path.getsize('EyeTracker-macOS.zip') / (1024*1024):.1f} MB)")
        
    elif system == 'linux':
        print("Creating Linux distribution package...")
        
        # Copy executable
        shutil.copy('dist/EyeTracker-Linux', 'release/')
        
        # Copy arduino directory
        if os.path.exists('arduino'):
            shutil.copytree('arduino', 'release/arduino')
        
        # Copy documentation
        for file in ['README.md', 'LICENSE']:
            if os.path.exists(file):
                shutil.copy(file, 'release/')
        
        # Create tar.gz file
        print("Creating EyeTracker-Linux.tar.gz...")
        with tarfile.open('EyeTracker-Linux.tar.gz', 'w:gz') as tar:
            for root, dirs, files in os.walk('release'):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, 'release')
                    tar.add(file_path, arcname)
        
        print(f"Created EyeTracker-Linux.tar.gz ({os.path.getsize('EyeTracker-Linux.tar.gz') / (1024*1024):.1f} MB)")

def show_build_warnings():
    """Show PyInstaller warnings if available"""
    # Updated path to match the spec file output
    warn_files = [
        'build/EyeTracker-macOS/warn-EyeTracker-macOS.txt',
        'build/EyeTracker/warn-EyeTracker.txt'
    ]
    
    for warn_file in warn_files:
        if os.path.exists(warn_file):
            print(f"\nPyInstaller warnings from {warn_file}:")
            print("-" * 50)
            with open(warn_file, 'r') as f:
                content = f.read()
                if content.strip():
                    print(content)
                else:
                    print("No warnings found.")
            print("-" * 50)
            break
    else:
        print("\nNo warning files found.")

def verify_macos_requirements():
    """Verify macOS-specific requirements for camera access"""
    system = platform.system().lower()
    if system != 'darwin':
        return
    
    print("\nVerifying macOS requirements...")
    
    # Check if we have camera permissions
    try:
        import subprocess
        result = subprocess.run(['system_profiler', 'SPCameraDataType'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and 'Camera' in result.stdout:
            print("✓ Camera hardware detected")
        else:
            print("⚠ Camera hardware not detected or accessible")
    except:
        print("⚠ Could not verify camera hardware")
    
    # Check for required system frameworks
    frameworks_to_check = [
        '/System/Library/Frameworks/AVFoundation.framework',
        '/System/Library/Frameworks/CoreMedia.framework',
        '/System/Library/Frameworks/CoreVideo.framework'
    ]
    
    for framework in frameworks_to_check:
        if os.path.exists(framework):
            print(f"✓ Found {os.path.basename(framework)}")
        else:
            print(f"⚠ Missing {os.path.basename(framework)}")

def main():
    """Main build function"""
    system_name = platform.system()
    print(f"Building for {system_name} ({platform.machine()})")
    print("=" * 50)
    
    # Verify we're in the project root
    if not os.path.exists('main.py'):
        print("ERROR: main.py not found. Please run this script from the project root directory.")
        sys.exit(1)
    
    try:
        print("Step 0: Verifying requirements...")
        if system_name == 'Darwin':
            verify_macos_requirements()
        
        print("\nStep 1: Cleaning previous builds...")
        clean_build()
        
        print("\nStep 2: Building application...")
        build_app()
        
        print("\nStep 3: Creating distribution package...")
        create_distribution_package()
        
        print("\nStep 4: Checking for warnings...")
        show_build_warnings()
        
        print(f"\nBuild process completed for {system_name}!")
        
        # Show dist folder contents
        print("\nBuilt executables in dist/ folder:")
        if os.path.exists('dist'):
            for item in os.listdir('dist'):
                item_path = os.path.join('dist', item)
                if os.path.isfile(item_path):
                    size = os.path.getsize(item_path) / (1024*1024)
                    print(f"  {item} ({size:.1f} MB)")
                elif os.path.isdir(item_path):
                    # For .app bundles, get directory size
                    try:
                        result = subprocess.run(['du', '-sh', item_path], capture_output=True, text=True)
                        if result.returncode == 0:
                            size_str = result.stdout.split()[0]
                            print(f"  {item}/ ({size_str})")
                        else:
                            print(f"  {item}/ (directory)")
                    except:
                        print(f"  {item}/ (directory)")
        
        # Show final package files
        print("\nGenerated distribution packages:")
        for file in os.listdir('.'):
            if file.endswith(('.zip', '.tar.gz')):
                size = os.path.getsize(file) / (1024*1024)
                print(f"  {file} ({size:.1f} MB)")
        
        # macOS specific post-build instructions
        if system_name == 'Darwin':
            print("\n" + "="*50)
            print("macOS POST-BUILD INSTRUCTIONS:")
            print("="*50)
            print("1. The app bundle is ready at: dist/EyeTracker.app")
            print("2. Before running, you may need to:")
            print("   - Right-click the app and select 'Open' the first time")
            print("   - Go to System Preferences > Security & Privacy > Camera")
            print("   - Allow EyeTracker to access the camera")
            print("3. If you get a segfault, try running from Terminal:")
            print("   cd dist && ./EyeTracker.app/Contents/MacOS/EyeTracker")
            print("   This will show detailed error messages")
            print("="*50)
        
    except Exception as e:
        print(f"Build failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()