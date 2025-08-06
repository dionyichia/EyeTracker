#!/usr/bin/env python3
"""
Debug tools for PyInstaller Qt6 macOS issues
"""

import subprocess
import os
import sys
import platform

def check_macos_bundle_integrity(app_path):
    """Check macOS app bundle integrity"""
    if not os.path.exists(app_path):
        print(f"ERROR: App bundle not found at {app_path}")
        return False
    
    print(f"=== Checking {app_path} ===")
    
    # Check bundle structure
    required_paths = [
        "Contents/Info.plist",
        "Contents/MacOS",
        "Contents/Resources"
    ]
    
    for path in required_paths:
        full_path = os.path.join(app_path, path)
        if os.path.exists(full_path):
            print(f"✓ Found {path}")
        else:
            print(f"✗ Missing {path}")
    
    # Check executable
    executable_path = None
    macos_dir = os.path.join(app_path, "Contents/MacOS")
    if os.path.exists(macos_dir):
        executables = [f for f in os.listdir(macos_dir) if os.access(os.path.join(macos_dir, f), os.X_OK)]
        if executables:
            executable_path = os.path.join(macos_dir, executables[0])
            print(f"✓ Found executable: {executables[0]}")
        else:
            print("✗ No executable found in MacOS directory")
    
    # Check library dependencies
    if executable_path:
        print("\n=== Library Dependencies ===")
        try:
            result = subprocess.run(['otool', '-L', executable_path], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(result.stdout)
            else:
                print(f"otool failed: {result.stderr}")
        except FileNotFoundError:
            print("otool not available")
    
    # Check for Qt plugins
    print("\n=== Qt Plugins ===")
    frameworks_path = os.path.join(app_path, "Contents/Frameworks")
    if os.path.exists(frameworks_path):
        qt_dirs = [d for d in os.listdir(frameworks_path) if 'qt' in d.lower()]
        print(f"Qt frameworks found: {qt_dirs}")
    
    plugins_path = os.path.join(app_path, "Contents/Resources")
    if os.path.exists(plugins_path):
        plugin_dirs = []
        for root, dirs, files in os.walk(plugins_path):
            if 'platforms' in dirs or 'imageformats' in dirs:
                plugin_dirs.append(root)
        print(f"Plugin directories: {plugin_dirs}")
    
    return True

def create_debug_runner(app_path):
    """Create a debug runner script"""
    debug_script = """#!/bin/bash
echo "=== EyeTracker Debug Runner ==="
echo "macOS Version: $(sw_vers -productVersion)"
echo "Architecture: $(uname -m)"
echo ""

# Set debug environment
export QT_DEBUG_PLUGINS=1
export DYLD_PRINT_LIBRARIES=1
export DYLD_PRINT_RPATHS=1
export DYLD_PRINT_SEARCHING=1

echo "=== Environment ==="
echo "QT_DEBUG_PLUGINS=$QT_DEBUG_PLUGINS"
echo "DYLD_LIBRARY_PATH=$DYLD_LIBRARY_PATH"
echo ""

echo "=== Starting Application ==="
cd "$(dirname "$0")"

# Try to run the app and capture output
./EyeTracker.app/Contents/MacOS/EyeTracker 2>&1 | tee crash_log.txt

echo ""
echo "=== Exit Code: $? ==="
echo "Debug output saved to crash_log.txt"
"""
    
    script_path = os.path.join(os.path.dirname(app_path), "debug_runner.sh")
    with open(script_path, 'w') as f:
        f.write(debug_script)
    os.chmod(script_path, 0o755)
    
    print(f"Created debug runner: {script_path}")
    return script_path

def fix_macos_library_paths(app_path):
    """Attempt to fix library path issues"""
    executable_path = None
    macos_dir = os.path.join(app_path, "Contents/MacOS")
    
    if os.path.exists(macos_dir):
        executables = [f for f in os.listdir(macos_dir) if os.access(os.path.join(macos_dir, f), os.X_OK)]
        if executables:
            executable_path = os.path.join(macos_dir, executables[0])
    
    if not executable_path:
        print("ERROR: No executable found to fix")
        return False
    
    print(f"=== Fixing library paths for {executable_path} ===")
    
    # Add common rpaths
    rpaths_to_add = [
        "@executable_path/../Frameworks",
        "@executable_path/../Resources",
        "@loader_path/../Frameworks",
        "@loader_path/../Resources"
    ]
    
    for rpath in rpaths_to_add:
        try:
            subprocess.run([
                'install_name_tool', '-add_rpath', rpath, executable_path
            ], check=False)  # Don't fail if rpath already exists
            print(f"✓ Added rpath: {rpath}")
        except subprocess.CalledProcessError as e:
            print(f"⚠ Could not add rpath {rpath}: {e}")
    
    return True

def create_fixed_spec_file():
    """Create an improved .spec file for macOS"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.building.api import PYZ, EXE, COLLECT, BUNDLE
from PyInstaller.building.build_main import Analysis

# Collect Qt plugins explicitly
def collect_qt_plugins():
    """Collect Qt plugins that might be missed"""
    qt_plugins = []
    
    try:
        import PyQt6
        qt_dir = os.path.join(os.path.dirname(PyQt6.__file__), 'Qt6')
        
        plugin_dirs = ['platforms', 'imageformats', 'iconengines', 'styles']
        for plugin_dir in plugin_dirs:
            plugin_path = os.path.join(qt_dir, 'plugins', plugin_dir)
            if os.path.exists(plugin_path):
                for plugin in os.listdir(plugin_path):
                    if plugin.endswith('.dylib'):
                        qt_plugins.append((
                            os.path.join(plugin_path, plugin),
                            os.path.join(plugin_dir, plugin)
                        ))
    except ImportError:
        pass
    
    return qt_plugins

# Analysis phase
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=collect_qt_plugins(),
    datas=[
        ('assets', 'assets'),
        ('arduino', 'arduino')
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.QtOpenGL',
        'PyQt6.QtOpenGLWidgets',
        'PyQt6.sip',
        'sip',
        # Additional Qt modules that might be needed
        'PyQt6.QtMultimedia',
        'PyQt6.QtMultimediaWidgets',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unused modules to reduce size
        'tkinter',
        'matplotlib',
        'scipy',
        'pandas',
    ],
    noarchive=False,
    optimize=0,
)

# Remove duplicate binaries
seen = set()
a.binaries = [x for x in a.binaries if not (x[0] in seen or seen.add(x[0]))]

pyz = PYZ(a.pure, a.zipped_data)

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
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='EyeTracker',
)

# App bundle
app = BUNDLE(
    coll,
    name='EyeTracker.app',
    icon=None,  # Add your icon path here if you have one
    bundle_identifier='com.eyetracker.app',
    version='1.0.0',
    info_plist={
        'CFBundleName': 'EyeTracker',
        'CFBundleDisplayName': 'EyeTracker',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleExecutable': 'EyeTracker',
        'CFBundleIdentifier': 'com.eyetracker.app',
        'NSCameraUsageDescription': 'This app requires camera access for eye tracking functionality.',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.14.0',
        'CFBundlePackageType': 'APPL',
        'CFBundleSignature': '????',
        # Prevent App Nap
        'NSAppSleepDisabled': True,
        # Qt-specific settings
        'QT_MAC_DISABLE_FOREGROUND_APPLICATION_TRANSFORM': '1',
    },
)
'''
    
    with open('EyeTracker-Fixed.spec', 'w') as f:
        f.write(spec_content)
    
    print("Created improved spec file: EyeTracker-Fixed.spec")
    return 'EyeTracker-Fixed.spec'

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python debug_tools.py check <path-to-app>     # Check app bundle")
        print("  python debug_tools.py fix <path-to-app>       # Fix library paths")
        print("  python debug_tools.py spec                    # Create improved spec")
        print("  python debug_tools.py debug <path-to-app>     # Create debug runner")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'check' and len(sys.argv) >= 3:
        app_path = sys.argv[2]
        check_macos_bundle_integrity(app_path)
    
    elif command == 'fix' and len(sys.argv) >= 3:
        app_path = sys.argv[2]
        fix_macos_library_paths(app_path)
    
    elif command == 'spec':
        create_fixed_spec_file()
    
    elif command == 'debug' and len(sys.argv) >= 3:
        app_path = sys.argv[2]
        create_debug_runner(app_path)
    
    else:
        print("Invalid command or missing arguments")
        sys.exit(1)

if __name__ == '__main__':
    main()