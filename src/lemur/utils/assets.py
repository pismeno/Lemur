import os
from pathlib import Path

LEMUR_ROOT = Path(__file__).resolve().parent.parent
LEMUR_PRIVATE_PATH = LEMUR_ROOT / "private"
LEMUR_PUBLIC_PATH = LEMUR_ROOT / "public"

PROJECT_ROOT_PATH = Path(os.getcwd())
PRIVATE_PATH = PROJECT_ROOT_PATH / "private"
PUBLIC_PATH = PROJECT_ROOT_PATH / "public"

def get_public_file_contents(path: str) -> str:
    clean_path = path.lstrip("/")
    
    if clean_path.startswith("lemur/"):
        relative_path = clean_path.removeprefix("lemur/")
        return _get_file_contents(LEMUR_PUBLIC_PATH / relative_path)
    
    return _get_file_contents(PUBLIC_PATH / clean_path)

def get_private_file_contents(path: str) -> str:
    clean_path = path.lstrip("/")
    
    if clean_path.startswith("lemur/"):
        relative_path = clean_path.removeprefix("lemur/")
        return _get_file_contents(LEMUR_PRIVATE_PATH / relative_path)
    
    return _get_file_contents(PRIVATE_PATH / clean_path)

def _get_file_contents(path: str) -> str:
    if not path.exists():
        raise FileNotFoundError(f"File not found at {path}")
        
    with open(path, "r", encoding="utf-8") as file:
        return file.read()