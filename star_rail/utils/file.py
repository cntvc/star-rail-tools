import json
import os
from pathlib import Path


def save_json(full_path: str | Path, data):
    path = Path(full_path)
    os.makedirs(path.parent, exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, sort_keys=False, indent=4)


def load_json(full_path: str | Path) -> dict:
    with open(full_path, encoding="UTF-8") as file:
        data = json.load(file)
    return data
