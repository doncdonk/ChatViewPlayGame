# -*- mode: python ; coding: utf-8 -*-
# ChatViewPlayGame - PyInstaller spec

block_cipher = None

a = Analysis(
    ['game.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('icon.ico', '.'),        # アイコン
        ('img', 'img'),           # 競馬用画像（馬・ゲート）
        ('horserace.py', '.'),    # 競馬ロジック
        ('minesweeper.py', '.'),  # ViewBombロジック
        ('reversi.py', '.'),      # リバーシロジック
        ('twitch_client.py', '.'),# Twitch接続
        ('config.py', '.'),       # 設定管理
    ],
    hiddenimports=[
        'tkinter',
        'tkinter.font',
        'tkinter.colorchooser',
        'asyncio',
        'ssl',
        'json',
        'threading',
        'random',
        'time',
        'math',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'PIL.ImageGrab',
        'PIL.ImageOps',
        'numpy',
        'numpy.core',
        'numpy.core._multiarray_umath',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'pygame',
        'scipy',
        'matplotlib',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ChatViewPlayGame',
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
    icon='icon.ico',
    version_file=None,
)
