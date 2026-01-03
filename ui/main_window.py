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
    QListWidgetItem,
    QComboBox
)
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QClipboard
from PySide6.QtCore import Qt, QStringListModel

from structurizer.storage.history_manager import HistoryManager
from pathlib import Path
from datetime import datetime
import os
from structurizer.config import STORAGE_DIR
from structurizer.ui.detail_window import DetailWindow
from structurizer.ui.clipboard_utils import copy_file_content_to_clipboard
from structurizer.ui.file_clipboard import copy_file_to_clipboard_as_object
from structurizer.analyzer.project_analyzer import ProjectAnalyzer
from PySide6.QtGui import QKeySequence, QShortcut

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
        # Левая панель — история с поиском
        # =====================
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(5)  # Уменьшаем расстояние между элементами

        # Панель поиска
        search_panel = QWidget()
        search_layout = QHBoxLayout(search_panel)
        search_layout.setContentsMargins(0, 0, 0, 0)

        # Иконка поиска
        search_icon = QLabel("🔍")
        search_icon.setFixedWidth(20)

        # Поле поиска
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по истории...")
        self.search_input.setClearButtonEnabled(True)



        search_layout.addWidget(search_icon)
        search_layout.addWidget(self.search_input)
        # В метод _build_ui, после создания search_input:
        self.search_field_combo = QComboBox()
        self.search_field_combo.addItems([
            "Все поля",
            "Название",
            "Путь к проекту",
            "Описание",
            "Дата"
        ])
        self.search_field_combo.setFixedWidth(120)

        # Обновляем search_layout:
        search_layout.addWidget(search_icon)
        search_layout.addWidget(self.search_field_combo)  # Добавляем комбобокс
        search_layout.addWidget(self.search_input)
        # Добавляем панель поиска
        left_layout.addWidget(search_panel)

        # Список истории
        self.history_list = QListWidget()
        self.history_list.setMinimumWidth(320)
        self.history_list.setSizePolicy(
            QSizePolicy.Fixed, QSizePolicy.Expanding
        )
        left_layout.addWidget(self.history_list)

        # Информация о результатах поиска
        self.search_info_label = QLabel()
        self.search_info_label.setStyleSheet("color: gray; font-size: 10px;")
        self.search_info_label.hide()
        left_layout.addWidget(self.search_info_label)

        main_layout.addWidget(left_panel)

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
        # Подключаем сигналы
        # =====================
        self.browse_button.clicked.connect(self._on_browse_clicked)
        self.all_extensions_checkbox.toggled.connect(
            self.allowed_ext_input.setDisabled
        )
        self.start_button.clicked.connect(self._on_start_clicked)

        # Сигналы для поиска
        self.search_input.textChanged.connect(self._on_search_text_changed)

        # Настраиваем горячие клавиши
        self.setup_shortcuts()

        # Настраиваем автодополнение для поиска (опционально)
        self._setup_search_autocomplete()

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
    
    def _on_search_text_changed(self, text):
        """Обработчик изменения текста в поле поиска"""
        if text:
            self._perform_search()
        else:
            self._clear_search()

    def _perform_search(self):
        """Выполняет поиск по истории"""
        search_text = self.search_input.text().strip().lower()
        search_field = self.search_field_combo.currentText()

        if not search_text:
            self._clear_search()
            return

        all_items = self.history_manager.load()

        if not all_items:
            return

        self.history_list.clear()

        filtered_items = []
        for item in all_items:
            match = False

            if search_field == "Все поля":
                fields = [
                    item.get('display_name', '').lower(),
                    item.get('project_path', '').lower(),
                    item.get('description', '').lower(),
                ]
                match = any(search_text in field for field in fields)

            elif search_field == "Название":
                match = search_text in item.get('display_name', '').lower()

            elif search_field == "Путь к проекту":
                match = search_text in item.get('project_path', '').lower()

            elif search_field == "Описание":
                match = search_text in item.get('description', '').lower()

            elif search_field == "Дата":
                # Ищем в дате создания
                created_at = item.get('created_at', '').lower()
                match = search_text in created_at

            if match:
                filtered_items.append(item)

        for item in filtered_items:
            self._add_history_item_to_list(item)

        self._update_search_info(len(filtered_items), len(all_items))

    def _update_search_info(self, found, total):
        """Обновляет информацию о результатах поиска"""
        if found == total:
            self.search_info_label.hide()
        else:
            self.search_info_label.show()
            self.search_info_label.setText(f"Найдено: {found} из {total}")

            # Показываем подсказку для очистки
            if found == 0:
                self.search_info_label.setText(f"Ничего не найдено. Всего элементов: {total}")

    def _clear_search(self):
        """Очищает поиск и показывает все элементы"""
        self.search_input.clear()
        self.search_info_label.hide()
        self._load_history()  # Загружаем полный список

    def _add_history_item_to_list(self, item_data):
        """Добавляет элемент в список истории (вспомогательный метод)"""
        display_name = item_data.get('display_name', '')
        if not display_name:
            project_path = Path(item_data.get('project_path', ''))
            display_name = project_path.name if project_path.name else str(project_path)

        created_at = item_data.get('created_at', '')

        # Форматируем дату для отображения
        if created_at:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                date_str = dt.strftime("%d.%m.%Y %H:%M")
            except:
                date_str = created_at

            display_text = f"{display_name} ({date_str})"
        else:
            display_text = display_name

        list_item = QListWidgetItem(display_text)
        list_item.setData(Qt.UserRole, item_data)

        # Подсветка совпадений (опционально)
        if self.search_input.text():
            self._highlight_matches(list_item, display_text, item_data)

        self.history_list.addItem(list_item)

    def _highlight_matches(self, list_item, display_text, item_data):
        """Подсвечивает совпадения в тексте элемента"""
        search_text = self.search_input.text().lower()

        # Проверяем, есть ли совпадение в разных полях
        fields_to_check = [
            item_data.get('display_name', '').lower(),
            item_data.get('project_path', '').lower(),
            item_data.get('description', '').lower(),
        ]

        # Если есть совпадение, подсвечиваем элемент
        for field in fields_to_check:
            if search_text in field:
                # Устанавливаем жирный шрифт для найденных элементов
                font = list_item.font()
                font.setBold(True)
                list_item.setFont(font)

                # Можно добавить цвет фона
                list_item.setBackground(Qt.yellow)
                break
    def setup_shortcuts(self):
        """Настраивает горячие клавиши"""
        
        # Ctrl+F для фокуса на поле поиска
        search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        search_shortcut.activated.connect(self._focus_search_field)

        # Esc для очистки поиска
        esc_shortcut = QShortcut(QKeySequence("Esc"), self)
        esc_shortcut.activated.connect(self._clear_search)

    def _focus_search_field(self):
        """Устанавливает фокус в поле поиска"""
        self.search_input.setFocus()
        self.search_input.selectAll()
    
    def _setup_search_autocomplete(self):
        """Настраивает автодополнение для поиска"""
        from PySide6.QtCore import QStringListModel
        from PySide6.QtWidgets import QCompleter

        # Создаем модель для автодополнения
        self.search_completer = QCompleter()
        self.search_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.search_completer.setFilterMode(Qt.MatchContains)

        # Устанавливаем модель с данными из истории
        self._update_search_completer_model()

        # Настраиваем поле поиска
        self.search_input.setCompleter(self.search_completer)

    def _update_search_completer_model(self):
        """Обновляет модель автодополнения данными из истории"""
        items = self.history_manager.load()

        # Собираем уникальные строки для автодополнения
        completions = set()

        for item in items:
            completions.add(item.get('display_name', ''))
            completions.add(Path(item.get('project_path', '')).name)
            # Можно добавить другие поля

        # Удаляем пустые строки
        completions = {c for c in completions if c}

        # Создаем и устанавливаем модель
        model = QStringListModel(sorted(completions))
        self.search_completer.setModel(model)
