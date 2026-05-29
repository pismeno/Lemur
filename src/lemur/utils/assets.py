import os
from pathlib import Path

project_root_path = Path(os.getcwd())
private_path = project_root_path / "private"
public_path = project_root_path / "public"

def get_public_file_contents(path: str) -> str:
    return _get_file_contents(public_path / path)

def get_private_file_contents(path: str) -> str:
    return _get_file_contents(private_path / path)

def _get_file_contents(path: str) -> str:
    if not path.exists():
        raise FileNotFoundError(f"File not found at {path}")
        
    with open(path, "r", encoding="utf-8") as file:
        return file.read()