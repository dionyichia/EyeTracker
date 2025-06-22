# -*- mode: python ; coding: utf-8 -*-
import os
import sys

# Get the spec file directory
spec_root = os.path.dirname(os.path.abspath(SPECPATH))
project_root = os.path.abspath(os.path.join(spec_root, '../..'))

a = Analysis(
    [os.path.join(project_root, 'main.py')],
    pathex=[project_root],
    binaries=[],
    datas=[
        (os.path.join(project_root, 'assets'), 'assets'), 
        (os.path.join(project_root, 'arduino'), 'arduino')
    ],
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
    info_plist=os.path.join(spec_root, 'Info.plist')
)# -*- mode: python ; coding: utf-8 -*-
import os
import sys

# Get the spec file directory
spec_root = os.path.dirname(os.path.abspath(SPECPATH))
project_root = os.path.abspath(os.path.join(spec_root, '../..'))

a = Analysis(
    [os.path.join(project_root, 'main.py')],
    pathex=[project_root],
    binaries=[],
    datas=[
        (os.path.join(project_root, 'assets'), 'assets'), 
        (os.path.join(project_root, 'arduino'), 'arduino')
    ],
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
    info_plist=os.path.join(spec_root, 'Info.plist')
)