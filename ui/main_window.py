from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QListWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QLabel,
    QCheckBox,
    QFileDialog,
    QSizePolicy,
    QListWidgetItem
)
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QClipboard
from PySide6.QtCore import Qt
from structurizer.storage.history_manager import HistoryManager
from pathlib import Path
from datetime import datetime
import os
from structurizer.config import STORAGE_DIR
from structurizer.ui.detail_window import DetailWindow
from structurizer.ui.clipboard_utils import copy_file_content_to_clipboard
from structurizer.ui.file_clipboard import copy_file_to_clipboard_as_object
from structurizer.analyzer.project_analyzer import ProjectAnalyzer

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Project Analyzer")
        self.resize(600, 350)
        
        self.history_manager = HistoryManager(base_dir=STORAGE_DIR)
        self._build_ui()
        self._load_history()

    def _load_history(self):
        """Загружает историю анализов"""
        self.history_list.clear()

        items = self.history_manager.load()

        for item in items:
            display_name = item.get('display_name', '')
            if not display_name:
                project_path = Path(item.get('project_path', ''))
                display_name = project_path.name if project_path.name else str(project_path)

            created_at = item.get('created_at', '')
            if created_at:
                display_text = f"{display_name} ({created_at})"
            else:
                display_text = display_name

            list_item = QListWidgetItem(display_text)
            list_item.setData(Qt.UserRole, item)
            self.history_list.addItem(list_item)

    def _build_ui(self):
        central = QWidget(self)
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)

        # =====================
        # Левая панель — история
        # =====================
        self.history_list = QListWidget()
        self.history_list.setMinimumWidth(320)
        self.history_list.setSizePolicy(
            QSizePolicy.Fixed, QSizePolicy.Expanding
        )

        main_layout.addWidget(self.history_list)

        # =====================
        # Правая панель — настройки
        # =====================
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(10)

        # Путь к проекту
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Путь к проекту")

        self.browse_button = QPushButton("📂")
        self.browse_button.setFixedWidth(40)

        path_layout.addWidget(self.path_input)
        path_layout.addWidget(self.browse_button)

        right_layout.addLayout(path_layout)

        # Ignored dirs
        self.ignored_dirs_input = QLineEdit()
        self.ignored_dirs_input.setPlaceholderText(
            "Игнорируемые папки (через ;)"
        )
        right_layout.addWidget(QLabel("Запрещённые папки:"))
        right_layout.addWidget(self.ignored_dirs_input)

        # Ignored files
        self.ignored_files_input = QLineEdit()
        self.ignored_files_input.setPlaceholderText(
            "Игнорируемые файлы (через ;)"
        )
        right_layout.addWidget(QLabel("Запрещённые файлы:"))
        right_layout.addWidget(self.ignored_files_input)

        # Allowed extensions
        self.allowed_ext_input = QLineEdit()
        self.allowed_ext_input.setPlaceholderText(
            "Разрешённые расширения (.py; .js; .cs)"
        )

        self.all_extensions_checkbox = QCheckBox("Анализировать все расширения")

        right_layout.addWidget(QLabel("Разрешённые расширения:"))
        right_layout.addWidget(self.allowed_ext_input)
        right_layout.addWidget(self.all_extensions_checkbox)

        # Spacer
        right_layout.addStretch()

        self.history_list.itemClicked.connect(self._on_history_item_clicked)
        self.history_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.history_list.customContextMenuRequested.connect(
            self._on_history_context_menu
        )

        # Кнопка запуска
        self.start_button = QPushButton("Начать анализ")
        self.start_button.setFixedHeight(40)
        right_layout.addWidget(self.start_button)

        main_layout.addWidget(right_panel)

        # =====================
        # Сигналы (пока пустые)
        # =====================
        self.browse_button.clicked.connect(self._on_browse_clicked)
        self.all_extensions_checkbox.toggled.connect(
            self.allowed_ext_input.setDisabled
        )
        self.start_button.clicked.connect(self._on_start_clicked)

    # =====================
    # Заглушки обработчиков
    # =====================
    def _open_result_file(self, entry):
        """Открывает файл результата"""
        output_file = Path(entry["output_file"])
        if output_file.exists():
            import os
            os.startfile(str(output_file))
        else:
            self._show_error("Файл не найден")

    def _open_in_explorer(self, entry):
        """Открывает проводник с файлом"""
        output_file = Path(entry["output_file"])
        if output_file.exists():
            import os
            # Открываем папку и выделяем файл
            os.system(f'explorer /select,"{output_file}"')
        else:
            self._show_error("Файл не найден")

    def _copy_to_clipboard(self, entry):
        """Копирует путь к файлу в буфер обмена"""
        output_file = Path(entry["output_file"])

        clipboard = QApplication.clipboard()
        clipboard.setText(str(output_file))


    def _delete_history_item_by_id(self, item_id):
        """Удаляет элемент истории по ID"""
        success = self.history_manager.remove(item_id, delete_output=True)
        if success:
            self._load_history()  # Обновляем список
            QMessageBox.information(self, "Удалено", "Элемент успешно удален")
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось удалить элемент")


    def _delete_history_item(self, entry, item):
        """Удаляет элемент истории"""
        from PySide6.QtWidgets import QMessageBox

        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Удалить запись {Path(entry['project_path']).name}?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            success = self.history_manager.remove(entry["id"])
            if success:
                self.history_list.takeItem(self.history_list.row(item))
                self._show_info("Запись удалена")
            else:
                self._show_error("Ошибка при удалении")
    def _on_history_item_clicked(self, item):
        """Открывает окно с деталями элемента при клике"""
        entry = item.data(Qt.UserRole)
        if entry:
            self._open_detail_window(entry)

    def _open_detail_window(self, history_item):
        """Открывает окно с деталями элемента"""
        detail_window = DetailWindow(
            history_item=history_item,
            history_manager=self.history_manager,
            parent=self
        )

        # Подключаем сигнал обновления
        detail_window.item_updated.connect(self._on_item_updated)

        detail_window.exec()
    def _on_item_updated(self, updated_item):
        """Обновляет элемент в списке после сохранения изменений"""
        self._load_history()  # Перезагружаем список

    def _on_browse_clicked(self):
        """Открывает диалог выбора папки"""
        dir_path = QFileDialog.getExistingDirectory(
            self, 
            "Выберите папку проекта"
        )
    
        if dir_path:
            self.path_input.setText(dir_path)

    def _on_history_context_menu(self, pos):
        """Показывает контекстное меню для элемента истории"""
        item = self.history_list.itemAt(pos)
        if not item:
            return

        entry = item.data(Qt.UserRole)
        if not entry:
            return

        from PySide6.QtWidgets import QMenu

        menu = QMenu()

        rename_action = menu.addAction("✏️ Переименовать")
        open_action = menu.addAction("📄 Открыть файл")
        open_in_explorer_action = menu.addAction("📂 Открыть в проводнике")
        copy_file_object_action = menu.addAction("📁 Копировать файл (как объект)")
        copy_file_action = menu.addAction("📋 Копировать содержимое")
        copy_path_action = menu.addAction("📋 Копировать путь")
        menu.addSeparator()
        delete_action = menu.addAction("🗑 Удалить")

        action = menu.exec(self.history_list.mapToGlobal(pos))
        if action == copy_file_object_action:
            self._copy_file_as_object(entry)
        elif action == copy_file_action:
            self._copy_file_to_clipboard(entry)
        elif action == rename_action:
            self._open_detail_window(entry)
        elif action == open_action:
            self._open_result_file(entry)
        elif action == open_in_explorer_action:
            self._open_in_explorer(entry)
        elif action == copy_path_action:
            self._copy_to_clipboard(entry)
        elif action == delete_action:
            self._delete_history_item(entry, item)

    def _copy_file_to_clipboard(self, entry):
        """Копирует содержимое файла в буфер обмена"""
        output_file = Path(entry.get('output_file', ''))
        if output_file.exists():
            copy_file_content_to_clipboard(output_file, self)
        else:
            self._show_error("Файл не найден")


    def _copy_file_as_object(self, entry):
        """Копирует файл как объект в буфер обмена"""
        output_file = Path(entry.get('output_file', ''))
        if output_file.exists():
            copy_file_to_clipboard_as_object(output_file, self)
        else:
            self._show_error("Файл не найден")


    def _on_start_clicked(self):
        """Запускает анализ проекта"""
        project_path_str = self.path_input.text().strip()

        if not project_path_str:
            self._show_error("Укажите путь к проекту")
            return

        project_path = Path(project_path_str)

        if not project_path.exists():
            self._show_error(f"Путь не существует: {project_path}")
            return

        ignored_dirs = [
            d.strip() for d in self.ignored_dirs_input.text().split(';') 
            if d.strip()
        ]
        ignored_files = [
            f.strip() for f in self.ignored_files_input.text().split(';') 
            if f.strip()
        ]

        if self.all_extensions_checkbox.isChecked():
            allowed_extensions = None
        else:
            allowed_extensions = [
                ext.strip() for ext in self.allowed_ext_input.text().split(';') 
                if ext.strip()
            ]

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        project_name = project_path.name or "project"
        output_filename = f"{project_name}_{timestamp}.txt"
        output_file = self.history_manager.outputs_dir / output_filename

        try:
            analyzer = ProjectAnalyzer(
                root_dir=project_path,
                output_file=output_file,
                ignored_dirs=ignored_dirs,
                ignored_files=ignored_files,
                allowed_extensions=allowed_extensions
            )

            analyzer.run()

            # Подсчитываем количество строк в результате
            line_count = 0
            if output_file.exists():
                with open(output_file, 'r', encoding='utf-8') as f:
                    line_count = sum(1 for _ in f)

            # Добавляем в историю
            settings = {
                "ignored_dirs": ignored_dirs,
                "ignored_files": ignored_files,
                "allowed_extensions": allowed_extensions
            }

            history_item = self.history_manager.add(
                project_path=project_path,
                output_file=output_file,
                settings=settings
            )

            # Обновляем счетчик строк (если метод add вернул словарь)
            if history_item and isinstance(history_item, dict):
                self.history_manager.update(
                    history_item['id'],
                    line_count=line_count
                )

                # Обновляем локальную копию для немедленного отображения
                history_item['line_count'] = line_count

            # Обновляем список
            self._load_history()

            # Показываем сообщение об успехе
            self._show_info(f"Анализ завершен. Строк: {line_count}")

        except Exception as e:
            self._show_error(f"Ошибка при анализе: {str(e)}")


    def _show_error(self, message):
        """Показывает сообщение об ошибке"""
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.critical(self, "Ошибка", message)


    def _show_info(self, message):
        """Показывает информационное сообщение"""
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Информация", message)
