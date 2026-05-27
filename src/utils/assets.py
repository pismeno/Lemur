import os
from pathlib import Path

def get_file_contents(path: str) -> str:
    project_root = Path(os.getcwd())
    asset_file_path = project_root / "assets" / path

    if not asset_file_path.exists():
        raise FileNotFoundError(f"Asset file not found at {asset_file_path}")
        
    with open(asset_file_path, "r", encoding="utf-8") as file:
        return file.read()