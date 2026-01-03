import sys
import os
from pathlib import Path
from setuptools import setup, find_packages

# Устанавливаем правильную кодировку для Windows
if sys.platform == "win32":
    import locale
    if os.environ.get("PYTHONUTF8", "0") != "1":
        locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

setup(
    name="structurizer",
    version="1.0.0",
    description="Анализатор структуры проектов",
    author="X",
    packages=find_packages(),
    install_requires=[
        "PySide6>=6.5.0",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "structurizer=structurizer.app:main",
        ],
    },
)