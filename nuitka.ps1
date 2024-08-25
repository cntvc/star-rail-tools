python -m nuitka `
    star_rail/main.py `
    --standalone `
    --nofollow-import-to=loguru,pydantic,aiosqlite,pyperclip,xlsxwriter,textual,pycryptodome `
    --output-dir=dist `
    --windows-icon-from-ico=resource/hsr.ico `
    --output-filename="Launcher" `
    --include-data-dir="star_rail/tui/tcss"="star_rail/tui/tcss" `
    --include-module=aiohttp`

$package_list = @(

)
