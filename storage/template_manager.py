# storage/template_manager.py

import json
from pathlib import Path
from typing import Dict, List, Optional
import uuid
from datetime import datetime


class TemplateManager:
    """Менеджер шаблонов настроек анализа"""
    
    def __init__(self, storage_dir: Path):
        self.storage_dir = Path(storage_dir)
        self.templates_file = self.storage_dir / "templates.json"
        self._ensure_storage()
    
    def _ensure_storage(self):
        """Создаёт необходимые директории и файлы"""
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        if not self.templates_file.exists():
            self._save_templates({
                "version": 1,
                "templates": []
            })
    
    def get_all(self) -> List[Dict]:
        """Возвращает все шаблоны"""
        data = self._load_templates()
        return data.get("templates", [])
    
    def get(self, template_id: str) -> Optional[Dict]:
        """Возвращает шаблон по ID"""
        templates = self.get_all()
        return next((t for t in templates if t["id"] == template_id), None)
    
    def create(self, name: str, settings: Dict) -> Dict:
        """Создаёт новый шаблон"""
        templates = self.get_all()
        
        template = {
            "id": str(uuid.uuid4()),
            "name": name,
            "settings": settings,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        
        templates.append(template)
        self._save_templates({
            "version": 1,
            "templates": templates
        })
        
        return template
    
    def update(self, template_id: str, name: str = None, settings: Dict = None) -> Optional[Dict]:
        """Обновляет шаблон"""
        templates = self.get_all()
        
        for template in templates:
            if template["id"] == template_id:
                if name is not None:
                    template["name"] = name
                if settings is not None:
                    template["settings"] = settings
                template["updated_at"] = datetime.now().isoformat()
                
                self._save_templates({
                    "version": 1,
                    "templates": templates
                })
                return template
        
        return None
    
    def delete(self, template_id: str) -> bool:
        """Удаляет шаблон"""
        templates = self.get_all()
        new_templates = [t for t in templates if t["id"] != template_id]
        
        if len(new_templates) != len(templates):
            self._save_templates({
                "version": 1,
                "templates": new_templates
            })
            return True
        return False
    
    def get_default_templates(self) -> List[Dict]:
        """Возвращает стандартные шаблоны"""
        return [
            {
                "id": "default_python",
                "name": "Python проект",
                "settings": {
                    "ignored_dirs": ["__pycache__", ".pytest_cache", ".venv", "venv", "env", ".env", "node_modules", ".git", ".idea", ".vscode", ".mypy_cache"],
                    "ignored_files": [".gitignore", "requirements.txt", "pyproject.toml", "setup.py", "*.pyc", "*.pyo", "*.pyd"],
                    "allowed_extensions": [".py"]
                }
            },
            {
                "id": "default_web",
                "name": "Веб проект (HTML/CSS/JS)",
                "settings": {
                    "ignored_dirs": ["node_modules", ".git", ".idea", ".vscode", "dist", "build"],
                    "ignored_files": [".gitignore", "package.json", "package-lock.json", "yarn.lock", "webpack.config.js"],
                    "allowed_extensions": [".html", ".css", ".js", ".jsx", ".ts", ".tsx", ".json"]
                }
            },
            {
                "id": "default_all",
                "name": "Все файлы",
                "settings": {
                    "ignored_dirs": [".git", ".idea", ".vscode", "node_modules"],
                    "ignored_files": [".gitignore"],
                    "allowed_extensions": []
                }
            }
        ]
    
    def _load_templates(self) -> Dict:
        """Загружает шаблоны из файла"""
        try:
            with open(self.templates_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {"version": 1, "templates": []}
    
    def _save_templates(self, data: Dict):
        """Сохраняет шаблоны в файл"""
        with open(self.templates_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)