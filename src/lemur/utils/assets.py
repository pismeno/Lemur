import os
from pathlib import Path
from typing import overload, Literal

LEMUR_ROOT = Path(__file__).resolve().parent.parent
LEMUR_PRIVATE_PATH = LEMUR_ROOT / "private"
LEMUR_PUBLIC_PATH = LEMUR_ROOT / "public"

PROJECT_ROOT_PATH = Path(os.getcwd())
PRIVATE_PATH = PROJECT_ROOT_PATH / "private"
PUBLIC_PATH = PROJECT_ROOT_PATH / "public"

def get_public_file_contents(path: str, binary: bool = False) -> str | bytes:
    clean_path = path.lstrip("/")
    
    if clean_path.startswith("lemur/"):
        relative_path = clean_path.removeprefix("lemur/")
        return get_file_contents(LEMUR_PUBLIC_PATH, relative_path, binary=binary)
    
    return get_file_contents(PUBLIC_PATH, clean_path, binary=binary)

def get_private_file_contents(path: str, binary: bool = False) -> str | bytes:
    clean_path = path.lstrip("/")
    
    if clean_path.startswith("lemur/"):
        relative_path = clean_path.removeprefix("lemur/")
        return get_file_contents(LEMUR_PRIVATE_PATH, relative_path, binary=binary)
    
    return get_file_contents(PRIVATE_PATH, clean_path, binary=binary)

def get_dir_contents(path: str) -> tuple[list[str], list[str]]:
    clean_path = path.lstrip("/")
    
    if clean_path.startswith("lemur/"):
        relative_path = clean_path.removeprefix("lemur/")
        base_path = LEMUR_PUBLIC_PATH
        target_suffix = relative_path
    else:
        base_path = PUBLIC_PATH
        target_suffix = clean_path
        
    directory_path = get_safe_path(base_path, target_suffix, is_dir=True)
    return (
        [item.name for item in directory_path.iterdir() if item.is_dir()], # directories
        [item.name for item in directory_path.iterdir() if item.is_file()] # files
    )

def get_file_contents(path: Path, suffix_path: str, binary: bool = False) -> str | bytes:
    with open(get_safe_path(path, suffix_path), 'rb') as file:
        content = file.read()
        return content if binary else content.decode('utf-8')

def get_safe_path(base_path: Path, suffix_path: str, is_dir: bool = False) -> Path:
    clean_suffix = suffix_path.lstrip("/")
    
    resolved_base = base_path.resolve()
    target_path = (resolved_base / clean_suffix).resolve()
    
    if not target_path.is_relative_to(resolved_base):
        raise PermissionError("Access Denied: Path traversal attempt detected.")

    if not target_path.exists():
        raise FileNotFoundError("The requested path could not be found.")
    
    # Check for file or directory based on expected type
    if is_dir and not target_path.is_dir():
        raise NotADirectoryError("The requested path is not a directory.")
    if not is_dir and not target_path.is_file():
        raise FileNotFoundError("The requested path is not a file.")
    
    return target_path