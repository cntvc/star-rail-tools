# -*- mode: python ; coding: utf-8 -*-


block_cipher = None

exe_name = "StarRailTools"

src_root_dir = "star_rail/"

file_list = [
    src_root_dir + "__init__.py",
    src_root_dir + "constant.py",
    src_root_dir + "exceptions.py",
    src_root_dir + "main.py",

    src_root_dir + "config/__init__.py",

    src_root_dir + "module/__init__.py",
    src_root_dir + "module/clipboard.py",
    src_root_dir + "module/menu.py",
    src_root_dir + "module/update.py",
    src_root_dir + "module/user.py",

    src_root_dir + "module/gacha/__init__.py",
    src_root_dir + "module/gacha/gacha_log.py",
    src_root_dir + "module/gacha/gacha_url.py",
    src_root_dir + "module/gacha/metadata.py",

    src_root_dir + "utils/__init__.py",
    src_root_dir + "utils/log.py",
    src_root_dir + "utils/functional.py",
]

icon_path = "resource/sr.ico"

default_settings = "star_rail/config/default_settings.toml"

data_list = [
    (icon_path, icon_path),
    (default_settings, "star_rail/config")
]

a = Analysis(
    file_list,
    pathex=[],
    binaries=[],
    datas=data_list,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name=exe_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
)
