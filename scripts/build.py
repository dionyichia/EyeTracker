import subprocess
import os
import shutil

def clean_build():
    """Clean previous build artifacts"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
    
    # Clean .pyc files
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.pyc'):
                os.remove(os.path.join(root, file))

def build_app():
    """Build the application using PyInstaller"""
    cmd = [
        'pyinstaller',
        '--noconfirm',
        '--onefile',
        '--windowed',
        '--name=EyeTracker',
        '--add-data=assets:assets',
        '--add-data=arduino:arduino',
        'main.py'
    ]
    
    subprocess.run(cmd, check=True)

if __name__ == "__main__":
    print("Cleaning previous builds...")
    clean_build()
    print("Building application...")
    build_app()
    print("Build complete!")
