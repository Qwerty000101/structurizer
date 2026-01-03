import sys
import os
from pathlib import Path

def get_base_dir():
    """Возвращает базовую директорию в зависимости от режима запуска"""
    if getattr(sys, 'frozen', False):
        # Режим EXE
        return Path(sys.executable).parent
    else:
        # Режим разработки
        return Path(__file__).resolve().parent

def get_storage_dir():
    """Возвращает путь к директории storage"""
    base = get_base_dir()
    storage_dir = base / "storage"
    storage_dir.mkdir(exist_ok=True)
    return storage_dir

BASE_DIR = get_base_dir()
STORAGE_DIR = get_storage_dir()