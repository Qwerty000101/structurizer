import os
from pathlib import Path
from typing import Iterable, Optional, Set


class ProjectAnalyzer:
    def __init__(
        self,
        root_dir: Path,
        output_file: Path,
        ignored_dirs: Optional[Iterable[str]] = None,
        ignored_files: Optional[Iterable[str]] = None,
        allowed_extensions: Optional[Iterable[str]] = None,
    ):
        self.root_dir: Path = Path(root_dir).resolve()
        self.output_file: Path = Path(output_file).resolve()

        if not self.root_dir.exists() or not self.root_dir.is_dir():
            raise ValueError(f"Корневая директория не существует: {self.root_dir}")

        self.ignored_dirs: Set[str] = set(ignored_dirs or [])
        self.ignored_files: Set[str] = set(ignored_files or [])
        self.allowed_extensions: Set[str] = set(
            ext.lower() for ext in (allowed_extensions or [])
        )

        self._file = None

    # =====================
    # Публичный API
    # =====================

    def run(self) -> None:
        """
        Запускает анализ проекта и записывает результат в output_file.
        """
        self.output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(self.output_file, "w", encoding="utf-8") as f:
            self._file = f

            self._write(f"Анализ проекта: {self.root_dir}\n\n")
            self._write("Структура проекта:\n")
            self._print_project_structure(self.root_dir)
            self._write("\nТекст из файлов проекта:\n")
            self._print_file_contents(self.root_dir)
            self._write(
                f"\nАнализ завершен. Результаты сохранены в {self.output_file}\n"
            )

            self._file = None

    # =====================
    # Внутренняя логика
    # =====================

    def _write(self, text: str) -> None:
        self._file.write(text)

    def _print_project_structure(
        self, current_dir: Path, indent: str = "", is_last: bool = True
    ) -> None:
        relative_path = current_dir.relative_to(self.root_dir)
        display_name = (
            self.root_dir.name if relative_path == Path(".") else current_dir.name
        )

        branch = "└── " if is_last else "├── "
        self._write(f"{indent}{branch}{display_name}\n")

        indent += "    " if is_last else "│   "

        try:
            items = sorted(current_dir.iterdir(), key=lambda p: p.name.lower())
        except (PermissionError, FileNotFoundError):
            self._write(f"{indent}└── <нет доступа>\n")
            return

        dirs = [
            p
            for p in items
            if p.is_dir() and p.name not in self.ignored_dirs
        ]

        files = [
            p
            for p in items
            if p.is_file() and p.name not in self.ignored_files
        ]

        for i, dir_path in enumerate(dirs):
            is_last_dir = (i == len(dirs) - 1) and not files
            self._print_project_structure(dir_path, indent, is_last_dir)

        for i, file_path in enumerate(files):
            is_last_file = i == len(files) - 1
            branch = "└── " if is_last_file else "├── "
            self._write(f"{indent}{branch}{file_path.name}\n")

    def _print_file_contents(self, root_dir: Path) -> None:
        for root, dirs, files in os.walk(root_dir):
            root_path = Path(root)

            dirs[:] = [
                d for d in dirs
                if d not in self.ignored_dirs
                and (root_path / d).resolve().is_relative_to(self.root_dir)
            ]

            files[:] = [
                f for f in files
                if f not in self.ignored_files
                and (root_path / f).resolve().is_relative_to(self.root_dir)
            ]

            for filename in files:
                file_path = root_path / filename
                file_ext = file_path.suffix.lower()

                if self.allowed_extensions and file_ext not in self.allowed_extensions:
                    continue

                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    self._write(f"\nСодержимое {file_path}:\n{content}\n")
                except UnicodeDecodeError:
                    self._write(
                        f"\nСодержимое {file_path}:\n<бинарный или нечитаемый файл>\n"
                    )
                except Exception as e:
                    self._write(
                        f"\nОшибка при чтении {file_path}: {e}\n"
                    )
