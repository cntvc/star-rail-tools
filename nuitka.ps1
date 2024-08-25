python -m nuitka `
    star_rail/main.py `
    --standalone `
    --output-dir=dist `
    --windows-icon-from-ico=resource/hsr.ico `
    --nofollow-imports `
    --follow-import-to=star_rail `
    --output-filename="StarRailTools" `
    --include-data-dir="star_rail/tui/tcss"="star_rail/tui/tcss" `
    --include-module=pygments.lexers.javascript `
