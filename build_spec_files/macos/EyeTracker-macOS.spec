# -*- mode: python ; coding: utf-8 -*-
import os
import sys

# Define paths - the spec file is in build_spec_files/macos/
# We need to go up two levels to reach the project root
spec_dir = os.path.dirname(os.path.abspath(SPECPATH))
project_root = os.path.abspath(os.path.join(spec_dir, '..', '..'))

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

a = Analysis(
    [main_py],
    pathex=[project_root],
    binaries=[],
    datas=[item for item in [
        (assets_path, 'assets') if os.path.exists(assets_path) else None,
        (arduino_path, 'arduino') if os.path.exists(arduino_path) else None,
    ] if item is not None],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

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
    console=False,
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
    name='EyeTracker',
)

app = BUNDLE(
    coll,
    name='EyeTracker.app',
    icon=None,
    bundle_identifier='com.eyetracker.app',
    info_plist=info_plist_path if os.path.exists(info_plist_path) else None,
)