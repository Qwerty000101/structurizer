import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class HistoryEntry:
    def __init__(self, project_path: Path, output_file: Path):
        self.project_path = project_path
        self.output_file = output_file

    def __str__(self):
        return str(self.project_path)
    
class HistoryManager:
    HISTORY_VERSION = 1

    def __init__(self, base_dir: Path):
        """
        base_dir — папка storage/
        """
        self.base_dir = Path(base_dir).resolve()
        self.outputs_dir = self.base_dir / "outputs"
        self.history_file = self.base_dir / "history.json"
        
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.outputs_dir.mkdir(parents=True, exist_ok=True)

        if not self.history_file.exists():
            self._write_history({
                "version": self.HISTORY_VERSION,
                "items": []
            })

    # =====================
    # Публичный API
    # =====================

    def load(self) -> List[Dict]:
        """
        Загружает и возвращает список элементов истории.
        """
        data = self._read_history()
        return data.get("items", [])

    def add(
        self,
        project_path: Path,
        output_file: Path,
        settings: Dict
    ) -> Dict:
        """
        Добавляет новую запись в историю и возвращает её.
        """
        data = self._read_history()

        item = {
            "id": uuid.uuid4().hex[:8],
            "project_path": str(project_path),
            "output_file": str(output_file),
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "settings": settings,
        }

        data["items"].append(item)
        self._write_history(data)

        return item
    def get_all(self) -> List[Dict]:
        """
        Возвращает все сохранённые элементы истории.
        """
        return self.load()
    

    def remove(self, item_id: str, delete_output: bool = True) -> bool:
        """
        Удаляет запись по id.
        Если delete_output=True — удаляет и файл результата.
        """
        data = self._read_history()
        items = data.get("items", [])

        item = next((i for i in items if i["id"] == item_id), None)
        if not item:
            return False

        if delete_output:
            output_path = Path(item["output_file"])
            try:
                if output_path.exists():
                    output_path.unlink()
            except Exception:
                # Файл мог быть удалён вручную — это не критично
                pass

        data["items"] = [i for i in items if i["id"] != item_id]
        self._write_history(data)

        return True

    def get(self, item_id: str) -> Optional[Dict]:
        """
        Возвращает одну запись по id.
        """
        items = self.load()
        return next((i for i in items if i["id"] == item_id), None)

    # =====================
    # Внутренние методы
    # =====================

    def _read_history(self) -> Dict:
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            # Восстановление при повреждённом файле
            data = {
                "version": self.HISTORY_VERSION,
                "items": []
            }
            self._write_history(data)
            return data

    def _write_history(self, data: Dict) -> None:
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
