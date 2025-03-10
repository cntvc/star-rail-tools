# -*- mode: python ; coding: utf-8 -*-

# Create a one-file bundled executable

exe_name = "StarRailTools"

src_root_dir = "star_rail"

def find_files(folder_path, ext_type:str):
    file_list = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith(ext_type):
                file_list.append(os.path.join(root, file))
    return file_list


src_list = find_files(src_root_dir, '.py')


tcss_path = os.path.join(src_root_dir, "tui")
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
