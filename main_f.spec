# -*- mode: python ; coding: utf-8 -*-


block_cipher = None

exe_name = "StarRailTools"

src_root_dir = "star_rail"

def find_files(folder_path, ext_type:str):
    py_files = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith(ext_type):
                py_files.append(os.path.join(root, file))
    return py_files


src_list = find_files(src_root_dir, '.py')


tcss_path = src_root_dir + "/tui"+"/tcss"
tcss_file = find_files(tcss_path, ".tcss")
ui_res_list = [(file, tcss_path) for file in tcss_file]

icon_path = "resource/hsr.ico"

data_list = ui_res_list

a = Analysis(
    src_list,
    pathex=[],
    binaries=[],
    datas=data_list,
    hiddenimports=["textual.widgets._tab_pane"],
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
