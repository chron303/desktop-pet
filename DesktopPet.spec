# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = ['PIL._tkinter_finder', 'PIL.Image', 'PIL.ImageDraw', 'PIL.ImageFilter', 'PIL.ImageTk', 'pystray', 'pystray._win32', 'win32api', 'win32con', 'win32gui', 'win32process', 'winsound', 'ctypes.wintypes', 'urllib.request', 'speech_recognition', 'google.cloud.speech']
hiddenimports += collect_submodules('PIL')
hiddenimports += collect_submodules('pystray')


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('config.json', '.'), ('pet_save.json', '.')],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'pandas', 'scipy', 'pytest', 'IPython', 'notebook'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='DesktopPet',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icon.ico'],
)
