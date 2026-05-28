import os
from pathlib import Path

project_root_path = Path(os.getcwd())
assets_path = project_root_path / "assets"

def get_file_contents(path: str) -> str:
    asset_file_path = assets_path / path

    if not asset_file_path.exists():
        raise FileNotFoundError(f"Asset file not found at {asset_file_path}")
        
    with open(asset_file_path, "r", encoding="utf-8") as file:
        return file.read()