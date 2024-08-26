python -m nuitka `
    star_rail/main.py `
    --standalone `
    --nofollow-import-to=loguru,pydantic,aiosqlite,pyperclip,xlsxwriter,textual,pycryptodome `
    --windows-icon-from-ico=resource/hsr.ico `
    --output-filename="Launcher" `
    --include-data-dir="star_rail/tui/tcss"="star_rail/tui/tcss" `
    --include-module=aiohttp

$project_name = "StarRailTools"

$dist_dir = "main.dist"

$package_list = @(
    "textual",
    "typing_extensions.py",
    "win32_setctime.py",
    "rich",
    "pydantic",
    "pydantic_core",
    "annotated_types",
    "aiosqlite",
    "loguru",
    "colorama",
    "pyperclip",
    "xlsxwriter",
    "pygments"
)

$source_dir = ".venv\Lib\site-packages"

$target_dir = $dist_dir

foreach ($item in $package_list) {
    $source_path = Join-Path -Path $source_dir -ChildPath $item
    $target_path = Join-Path -Path $target_dir -ChildPath $item

    if (Test-Path -Path $source_path -PathType Container) {
        Copy-Item -Path $source_path -Destination $target_path -Recurse -Force
    } else {
        Copy-Item -Path $source_path -Destination $target_path -Force
    }
}

if ($env:GITHUB_ACTIONS) {
    Rename-Item -Path $target_dir -NewName $project_name
}
