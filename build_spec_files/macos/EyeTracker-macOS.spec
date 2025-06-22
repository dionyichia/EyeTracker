# -*- mode: python ; coding: utf-8 -*-
import os
import sys
import platform

# Get the correct project root path
# This spec file is in build_spec_files/macos/, so we need to go up 2 levels
spec_dir = os.path.dirname(os.path.abspath(SPECPATH))
project_root = os.path.abspath(os.path.join(spec_dir, '..'))

# Path to main.py from project root
main_py = os.path.join(project_root, 'main.py')

# Verify paths exist
if not os.path.exists(main_py):
    print(f"ERROR: main.py not found at {main_py}")
    print(f"Spec directory: {spec_dir}")
    print(f"Project root: {project_root}")
    print(f"Contents of project root: {os.listdir(project_root) if os.path.exists(project_root) else 'Directory not found'}")
    sys.exit(1)

# Paths for data files
assets_path = os.path.join(project_root, 'assets')
arduino_path = os.path.join(project_root, 'arduino')
info_plist_path = os.path.join(spec_dir, 'Info.plist')

print(f"Using main.py: {main_py}")
print(f"Using assets: {assets_path}")
print(f"Using arduino: {arduino_path}")
print(f"Using Info.plist: {info_plist_path}")
print(f"Project root: {project_root}")

# Collect all Python files from the app directory to ensure proper imports
app_modules = []
app_dir = os.path.join(project_root, 'app')
if os.path.exists(app_dir):
    for root, dirs, files in os.walk(app_dir):
        for file in files:
            if file.endswith('.py') and not file.startswith('__'):
                rel_path = os.path.relpath(os.path.join(root, file), project_root)
                module_name = rel_path.replace(os.sep, '.').replace('.py', '')
                app_modules.append(module_name)

print(f"Found app modules: {app_modules}")

# macOS specific hidden imports for camera and multimedia
macos_hidden_imports = [
    # OpenCV and camera access
    'cv2',
    'numpy',
    'numpy.core',
    'numpy.core._multiarray_umath',
    'numpy.core._multiarray_tests',
    
    # GUI frameworks
    'tkinter',
    'tkinter.ttk',
    'tkinter.filedialog',
    'tkinter.messagebox',
    
    # Multimedia frameworks
    'PIL', 'PIL.Image', 'PIL.ImageTk',
    
    # Threading and multiprocessing
    'threading',
    'multiprocessing',
    'concurrent.futures',
    
    # System and hardware access
    'platform',
    'subprocess',
    'ctypes',
    'ctypes.util',
    
    # App modules
] + app_modules

# macOS specific binaries and libraries
macos_binaries = []

# Try to find OpenCV libraries
try:
    import cv2
    cv2_path = cv2.__file__
    cv2_dir = os.path.dirname(cv2_path)
    
    # Look for OpenCV dynamic libraries
    for file in os.listdir(cv2_dir):
        if file.endswith('.dylib') or file.endswith('.so'):
            lib_path = os.path.join(cv2_dir, file)
            macos_binaries.append((lib_path, '.'))
    
    print(f"Found OpenCV libraries: {len(macos_binaries)} files")
except ImportError:
    print("WARNING: OpenCV not found - camera functionality may not work")

# System frameworks and libraries
system_frameworks = [
    '/System/Library/Frameworks/AVFoundation.framework/Versions/A/AVFoundation',
    '/System/Library/Frameworks/CoreMedia.framework/Versions/A/CoreMedia',
    '/System/Library/Frameworks/CoreVideo.framework/Versions/A/CoreVideo',
    '/System/Library/Frameworks/QuartzCore.framework/Versions/A/QuartzCore',
    '/System/Library/Frameworks/Accelerate.framework/Versions/A/Accelerate',
]

for framework in system_frameworks:
    if os.path.exists(framework):
        macos_binaries.append((framework, '.'))
        print(f"Including framework: {os.path.basename(framework)}")

a = Analysis(
    [main_py],
    pathex=[project_root, app_dir],  # Add app directory to Python path
    binaries=macos_binaries,
    datas=[item for item in [
        (assets_path, 'assets') if os.path.exists(assets_path) else None,
        (arduino_path, 'arduino') if os.path.exists(arduino_path) else None,
    ] if item is not None],
    hiddenimports=macos_hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary modules to reduce size
        'matplotlib',
        'scipy',
        'pandas',
        'jupyter',
        'notebook',
    ],
    noarchive=False,
    optimize=0,
)

# Remove duplicate entries
a.datas = list(set(a.datas))

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='EyeTracker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Set to True for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='EyeTracker-macOS',  # Changed to match build directory
)

app = BUNDLE(
    coll,
    name='EyeTracker.app',
    icon=None,
    bundle_identifier='com.eyetracker.app',
    info_plist=info_plist_path if os.path.exists(info_plist_path) else None,
    version='1.0.0',
)