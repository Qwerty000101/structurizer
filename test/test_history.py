from pathlib import Path
from storage.history_manager import HistoryManager

history = HistoryManager(Path("D:\\structurizer\\structurizer\\test\\storage"))

item = history.add(
    project_path=Path("D:\\structurizer\\structurizer\\test\\storage"),
    output_file=Path("D:\\structurizer\\structurizer\\test\\storage\\outputs\\test.txt"),
    settings={
        "ignored_dirs": [".git"],
        "ignored_files": ["secret.py"],
        "allowed_extensions": [".py"]
    }
)

print(item)
print(history.load())
history.remove(item["id"])
print(history.load())
