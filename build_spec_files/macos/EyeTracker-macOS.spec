# -*- mode: python ; coding: utf-8 -*-
import os
import sys
import platform

# More robust path detection
# First, try to find the project root by looking for main.py
def find_project_root():
    # Start from the current working directory (where PyInstaller is called from)
    current_dir = os.getcwd()
    print(f"Current working directory: {current_dir}")
    
    # Check if main.py is in the current directory
    if os.path.exists(os.path.join(current_dir, 'main.py')):
        print(f"Found main.py in current directory: {current_dir}")
        return current_dir
    
    # If not, try to find it relative to the spec file location
    spec_dir = os.path.dirname(os.path.abspath(SPECPATH))
    print(f"Spec file directory: {spec_dir}")
    
    # Go up two levels from the spec file (build_spec_files/macos/)
    project_from_spec = os.path.abspath(os.path.join(spec_dir, '..', '..'))
    if os.path.exists(os.path.join(project_from_spec, 'main.py')):
        print(f"Found main.py relative to spec file: {project_from_spec}")
        return project_from_spec
    
    # Last resort: search parent directories
    search_dir = current_dir
    for _ in range(5):  # Don't search too far up
        if os.path.exists(os.path.join(search_dir, 'main.py')):
            print(f"Found main.py in parent directory: {search_dir}")
            return search_dir
        search_dir = os.path.dirname(search_dir)
        if search_dir == os.path.dirname(search_dir):  # Reached root
            break
    
    raise FileNotFoundError("Could not find project root with main.py")

# Find the project root
project_root = find_project_root()

# Path to main.py from project root
main_py = os.path.join(project_root, 'main.py')

# Verify paths exist
if not os.path.exists(main_py):
    print(f"ERROR: main.py not found at {main_py}")
    print(f"Project root: {project_root}")
    print(f"Contents of project root: {os.listdir(project_root) if os.path.exists(project_root) else 'Directory not found'}")
    sys.exit(1)

# Paths for data files
assets_path = os.path.join(project_root, 'assets')
arduino_path = os.path.join(project_root, 'arduino')

# Look for Info.plist in multiple locations
info_plist_paths = [
    os.path.join(project_root, 'build_spec_files', 'macos', 'Info.plist'),
    os.path.join(os.path.dirname(SPECPATH), 'Info.plist'),
]

info_plist_path = None
for path in info_plist_paths:
    if os.path.exists(path):
        info_plist_path = path
        break

print(f"Using main.py: {main_py}")
print(f"Using assets: {assets_path} (exists: {os.path.exists(assets_path)})")
print(f"Using arduino: {arduino_path} (exists: {os.path.exists(arduino_path)})")
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
    print(f"OpenCV version: {cv2.__version__}")
    print(f"OpenCV path: {cv2_path}")
except ImportError as e:
    print(f"WARNING: OpenCV not found - {e}")
except Exception as e:
    print(f"ERROR with OpenCV: {e}")

# System frameworks and libraries - be more careful about what exists
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
    else:
        print(f"Framework not found: {framework}")

print(f"Total binaries to include: {len(macos_binaries)}")

# Build the data files list more carefully
datas = []
if os.path.exists(assets_path):
    datas.append((assets_path, 'assets'))
    print(f"Including assets directory")
else:
    print(f"Assets directory not found: {assets_path}")

if os.path.exists(arduino_path):
    datas.append((arduino_path, 'arduino'))
    print(f"Including arduino directory")
else:
    print(f"Arduino directory not found: {arduino_path}")

print(f"Data files to include: {len(datas)} directories")

a = Analysis(
    [main_py],
    pathex=[project_root] + ([app_dir] if os.path.exists(app_dir) else []),
    binaries=macos_binaries,
    datas=datas,
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
    info_plist=info_plist_path,
    version='1.0.0',
)