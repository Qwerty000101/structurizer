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
    QComboBox,
    QTabWidget, 
    QInputDialog, 
    QTextEdit, 
    QGroupBox, 
    QFormLayout,
    QApplication, 
    QMessageBox
)

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
from structurizer.storage.template_manager import TemplateManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Structurizer")
        self.resize(600, 350)
        self._set_window_icon()
        BASE_DIR = Path(__file__).resolve().parent.parent

        self.history_manager = HistoryManager(
            base_dir=BASE_DIR / "storage"
        )

        # Добавляем менеджер шаблонов
        self.template_manager = TemplateManager(
            storage_dir=BASE_DIR / "storage"
        )

        self._build_ui()
        self._load_history()
    
    # Переносим загрузку шаблонов в конец _build_ui

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
        left_layout.setSpacing(5)

        # Панель поиска
        search_panel = QWidget()
        search_layout = QHBoxLayout(search_panel)
        search_layout.setContentsMargins(0, 0, 0, 0)

        # Поле поиска с комбобоксом для выбора поля
        self.search_field_combo = QComboBox()
        self.search_field_combo.addItems([
            "Все поля",
            "Название",
            "Путь к проекту",
            "Описание",
            "Дата"
        ])
        self.search_field_combo.setFixedWidth(120)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по истории...")
        self.search_input.setClearButtonEnabled(True)

        search_layout.addWidget(self.search_field_combo)
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
        # Правая панель — вкладки
        # =====================
        self.tab_widget = QTabWidget()

        # Вкладка 1: Настройки анализа
        self.settings_tab = QWidget()
        self._build_settings_tab()  # Здесь создаётся start_button
        self.tab_widget.addTab(self.settings_tab, "Настройки анализа")

        # Вкладка 2: Шаблоны
        self.templates_tab = QWidget()
        self._build_templates_tab()
        self.tab_widget.addTab(self.templates_tab, "Шаблоны настроек")

        main_layout.addWidget(self.tab_widget)

        # =====================
        # Подключаем сигналы ПОСЛЕ создания всех виджетов
        # =====================
        # Сигналы для поиска
        self.search_input.textChanged.connect(self._on_search_text_changed)
        self.search_field_combo.currentTextChanged.connect(self._on_search_text_changed)

        # Сигналы для списка истории
        self.history_list.itemClicked.connect(self._on_history_item_clicked)
        self.history_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.history_list.customContextMenuRequested.connect(
            self._on_history_context_menu
        )

        # Сигнал для кнопки запуска (теперь start_button уже создан)
        self.start_button.clicked.connect(self._on_start_clicked)

        # Настраиваем горячие клавиши
        self.setup_shortcuts()

        # Загружаем шаблоны ПОСЛЕ создания всех виджетов
        self._load_templates()

        # Настраиваем автодополнение для поиска (опционально)
        self._setup_search_autocomplete()

    def _set_window_icon(self):
        """Устанавливает иконку окна"""
        base_dir = Path(__file__).resolve().parent.parent

        # Пробуем разные пути к иконке
        icon_paths = [
            base_dir / "icon.ico",
            base_dir / "ui" / "icons" / "icon.ico",
            base_dir / "ui" / "icons" / "app_icon.ico",
            base_dir / "icon.png",
        ]

        for icon_path in icon_paths:
            if icon_path.exists():
                try:
                    from PySide6.QtGui import QIcon
                    self.setWindowIcon(QIcon(str(icon_path)))
                    print(f"Иконка окна загружена: {icon_path}")
                    break
                except Exception as e:
                    print(f"Ошибка загрузки иконки {icon_path}: {e}")

    def _build_templates_tab(self):
        """Создаёт вкладку управления шаблонами"""
        layout = QVBoxLayout(self.templates_tab)

        # Список шаблонов
        templates_group = QGroupBox("Шаблоны")
        templates_layout = QVBoxLayout(templates_group)

        self.templates_list = QListWidget()
        self.templates_list.itemClicked.connect(self._on_template_item_clicked)
        self.templates_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.templates_list.customContextMenuRequested.connect(
            self._on_template_context_menu
        )

        templates_layout.addWidget(self.templates_list)

        # Кнопки управления
        buttons_layout = QHBoxLayout()

        self.add_template_button = QPushButton("➕ Добавить шаблон")
        self.add_template_button.clicked.connect(self._add_template)

        self.edit_template_button = QPushButton("✏️ Переименовать")
        self.edit_template_button.clicked.connect(self._edit_template)

        self.delete_template_button = QPushButton("🗑 Удалить")
        self.delete_template_button.clicked.connect(self._delete_template)

        self.apply_template_button = QPushButton("📋 Применить")
        self.apply_template_button.clicked.connect(self._apply_selected_template)

        buttons_layout.addWidget(self.add_template_button)
        buttons_layout.addWidget(self.edit_template_button)
        buttons_layout.addWidget(self.delete_template_button)
        buttons_layout.addWidget(self.apply_template_button)

        templates_layout.addLayout(buttons_layout)

        layout.addWidget(templates_group)

        # Детали шаблона
        details_group = QGroupBox("Детали шаблона")
        details_layout = QFormLayout(details_group)

        self.template_name_label = QLabel()
        self.template_created_label = QLabel()
        self.template_updated_label = QLabel()
        self.template_settings_text = QTextEdit()
        self.template_settings_text.setReadOnly(True)
        self.template_settings_text.setMaximumHeight(150)

        details_layout.addRow("Название:", self.template_name_label)
        details_layout.addRow("Создан:", self.template_created_label)
        details_layout.addRow("Обновлён:", self.template_updated_label)
        details_layout.addRow("Настройки:", self.template_settings_text)

        layout.addWidget(details_group)
        layout.addStretch()


    def _build_settings_tab(self):
        """Создаёт вкладку настроек анализа"""
        layout = QVBoxLayout(self.settings_tab)
        layout.setSpacing(10)

        # Панель выбора шаблона
        template_group = QGroupBox("Шаблон настроек")
        template_layout = QHBoxLayout(template_group)

        self.template_combo = QComboBox()
        self.template_combo.addItem("Выберите шаблон настроек", None)
        self.template_combo.currentIndexChanged.connect(self._on_template_selected)

        self.save_as_template_button = QPushButton("💾 Сохранить как шаблон")
        self.save_as_template_button.clicked.connect(self._save_current_as_template)

        template_layout.addWidget(QLabel("Шаблон:"))
        template_layout.addWidget(self.template_combo, 1)
        template_layout.addWidget(self.save_as_template_button)

        layout.addWidget(template_group)

        # Путь к проекту
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Путь к проекту")

        self.browse_button = QPushButton("📂")
        self.browse_button.setFixedWidth(40)

        path_layout.addWidget(self.path_input)
        path_layout.addWidget(self.browse_button)

        layout.addLayout(path_layout)

        # Ignored dirs
        self.ignored_dirs_input = QLineEdit()
        self.ignored_dirs_input.setPlaceholderText(
            "Игнорируемые папки (через ;)"
        )
        layout.addWidget(QLabel("Запрещённые папки:"))
        layout.addWidget(self.ignored_dirs_input)

        # Ignored files
        self.ignored_files_input = QLineEdit()
        self.ignored_files_input.setPlaceholderText(
            "Игнорируемые файлы (через ;)"
        )
        layout.addWidget(QLabel("Запрещённые файлы:"))
        layout.addWidget(self.ignored_files_input)

        # Allowed extensions
        self.allowed_ext_input = QLineEdit()
        self.allowed_ext_input.setPlaceholderText(
            "Разрешённые расширения (.py; .js; .cs)"
        )

        self.all_extensions_checkbox = QCheckBox("Анализировать все расширения")

        layout.addWidget(QLabel("Разрешённые расширения:"))
        layout.addWidget(self.allowed_ext_input)
        layout.addWidget(self.all_extensions_checkbox)

        # Spacer
        layout.addStretch()

        # Кнопка запуска
        self.start_button = QPushButton("Начать анализ")
        self.start_button.setFixedHeight(40)
        layout.addWidget(self.start_button)

        # Подключаем сигналы
        self.browse_button.clicked.connect(self._on_browse_clicked)
        self.all_extensions_checkbox.toggled.connect(
            self.allowed_ext_input.setDisabled
        )
    # =====================
    # Обработчики
    # =====================
    def _load_templates(self):
        """Загружает список шаблонов"""
        # Очищаем списки
        self.template_combo.clear()
        self.templates_list.clear()

        # Добавляем пустой элемент
        self.template_combo.addItem("-- Выберите шаблон --", None)

        # Загружаем шаблоны
        templates = self.template_manager.get_all()

        # Если шаблонов нет, добавляем стандартные
        if not templates:
            default_templates = self.template_manager.get_default_templates()
            for template in default_templates:
                self.template_manager.create(template["name"], template["settings"])

            # Перезагружаем
            templates = self.template_manager.get_all()

        # Заполняем комбобокс и список
        for template in templates:
            # В комбобокс
            self.template_combo.addItem(template["name"], template["id"])

            # В список
            item = QListWidgetItem(template["name"])
            item.setData(Qt.UserRole, template)
            self.templates_list.addItem(item)

        # Очищаем детали
        self._clear_template_details()

    def _clear_template_details(self):
        """Очищает детали шаблона"""
        self.template_name_label.setText("")
        self.template_created_label.setText("")
        self.template_updated_label.setText("")
        self.template_settings_text.clear()

    def _on_template_item_clicked(self, item):
        """Обработчик клика по шаблону в списке"""
        template = item.data(Qt.UserRole)
        if template:
            self._show_template_details(template)

    def _show_template_details(self, template):
        """Показывает детали шаблона"""
        self.template_name_label.setText(template.get("name", ""))

        # Форматируем даты
        created_at = template.get("created_at", "")
        if created_at:
            try:
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                self.template_created_label.setText(dt.strftime("%d.%m.%Y %H:%M"))
            except:
                self.template_created_label.setText(created_at)

        updated_at = template.get("updated_at", "")
        if updated_at:
            try:
                dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                self.template_updated_label.setText(dt.strftime("%d.%m.%Y %H:%M"))
            except:
                self.template_updated_label.setText(updated_at)

        # Форматируем настройки
        settings = template.get("settings", {})
        text = []
        if "ignored_dirs" in settings:
            text.append(f"Папки: {', '.join(settings['ignored_dirs'])}")
        if "ignored_files" in settings:
            text.append(f"Файлы: {', '.join(settings['ignored_files'])}")
        if "allowed_extensions" in settings:
            exts = settings['allowed_extensions']
            if exts:
                text.append(f"Расширения: {', '.join(exts)}")
            else:
                text.append("Расширения: все")

        self.template_settings_text.setText("\n".join(text))

    def _on_template_selected(self, index):
        """Обработчик выбора шаблона в комбобоксе"""
        template_id = self.template_combo.currentData()
        if template_id:
            template = self.template_manager.get(template_id)
            if template:
                self._apply_template_settings(template)

    def _apply_template_settings(self, template):
        """Применяет настройки шаблона к полям"""
        settings = template.get("settings", {})

        # Заполняем поля
        if "ignored_dirs" in settings:
            self.ignored_dirs_input.setText("; ".join(settings["ignored_dirs"]))

        if "ignored_files" in settings:
            self.ignored_files_input.setText("; ".join(settings["ignored_files"]))

        if "allowed_extensions" in settings:
            exts = settings["allowed_extensions"]
            if exts:
                self.allowed_ext_input.setText("; ".join(exts))
                self.all_extensions_checkbox.setChecked(False)
                self.allowed_ext_input.setEnabled(True)
            else:
                self.allowed_ext_input.clear()
                self.all_extensions_checkbox.setChecked(True)
                self.allowed_ext_input.setEnabled(False)

    def _apply_selected_template(self):
        """Применяет выбранный шаблон к текущим настройкам"""
        current_item = self.templates_list.currentItem()
        if current_item:
            template = current_item.data(Qt.UserRole)
            if template:
                self._apply_template_settings(template)
                # Переключаемся на вкладку настроек
                self.tab_widget.setCurrentWidget(self.settings_tab)

                # Устанавливаем выбранный шаблон в комбобоксе
                index = self.template_combo.findData(template["id"])
                if index >= 0:
                    self.template_combo.setCurrentIndex(index)

    def _save_current_as_template(self):
        """Сохраняет текущие настройки как новый шаблон"""
        # Получаем имя шаблона
        name, ok = QInputDialog.getText(
            self,
            "Создание шаблона",
            "Введите название шаблона:",
            QLineEdit.Normal,
            ""
        )

        if ok and name:
            # Собираем настройки
            settings = self._get_current_settings()

            # Создаём шаблон
            template = self.template_manager.create(name, settings)

            # Обновляем списки
            self._load_templates()

            # Выбираем новый шаблон
            index = self.template_combo.findData(template["id"])
            if index >= 0:
                self.template_combo.setCurrentIndex(index)

            QMessageBox.information(self, "Успех", f"Шаблон '{name}' создан!")

    def _get_current_settings(self):
        """Возвращает текущие настройки из полей"""
        ignored_dirs = [
            d.strip() for d in self.ignored_dirs_input.text().split(';') 
            if d.strip()
        ]

        ignored_files = [
            f.strip() for f in self.ignored_files_input.text().split(';') 
            if f.strip()
        ]

        if self.all_extensions_checkbox.isChecked():
            allowed_extensions = []
        else:
            allowed_extensions = [
                ext.strip() for ext in self.allowed_ext_input.text().split(';') 
                if ext.strip()
            ]

        return {
            "ignored_dirs": ignored_dirs,
            "ignored_files": ignored_files,
            "allowed_extensions": allowed_extensions
        }

    def _add_template(self):
        """Добавляет новый шаблон"""
        self._save_current_as_template()

    def _edit_template(self):
        """Редактирует выбранный шаблон"""
        current_item = self.templates_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Ошибка", "Выберите шаблон для редактирования")
            return

        template = current_item.data(Qt.UserRole)
        if not template:
            return

        # Запрашиваем новое имя
        name, ok = QInputDialog.getText(
            self,
            "Редактирование шаблона",
            "Введите новое название шаблона:",
            QLineEdit.Normal,
            template.get("name", "")
        )

        if ok and name:
            # Получаем текущие настройки
            settings = self._get_current_settings()

            # Обновляем шаблон
            updated = self.template_manager.update(
                template["id"],
                name=name,
                settings=settings
            )

            if updated:
                self._load_templates()
                QMessageBox.information(self, "Успех", "Шаблон обновлён!")

    def _delete_template(self):
        """Удаляет выбранный шаблон"""
        current_item = self.templates_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Ошибка", "Выберите шаблон для удаления")
            return

        template = current_item.data(Qt.UserRole)
        if not template:
            return

        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы уверены, что хотите удалить шаблон '{template.get('name', '')}'?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            success = self.template_manager.delete(template["id"])
            if success:
                self._load_templates()
                self._clear_template_details()
                QMessageBox.information(self, "Успех", "Шаблон удалён!")
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось удалить шаблон")

    def _on_template_context_menu(self, pos):
        """Контекстное меню для шаблонов"""
        item = self.templates_list.itemAt(pos)
        if not item:
            return

        menu = QMenu()

        apply_action = menu.addAction("📋 Применить")
        edit_action = menu.addAction("✏️ Редактировать")
        delete_action = menu.addAction("🗑 Удалить")
        menu.addSeparator()
        duplicate_action = menu.addAction("➕ Дублировать")

        action = menu.exec(self.templates_list.mapToGlobal(pos))

        template = item.data(Qt.UserRole)
        if not template:
            return

        if action == apply_action:
            self._apply_template_settings(template)
            self.tab_widget.setCurrentWidget(self.settings_tab)
        elif action == edit_action:
            self._edit_template()
        elif action == delete_action:
            self._delete_template()
        elif action == duplicate_action:
            self._duplicate_template(template)

    def _duplicate_template(self, template):
        """Создаёт копию шаблона"""
        name, ok = QInputDialog.getText(
            self,
            "Дублирование шаблона",
            "Введите название для копии:",
            QLineEdit.Normal,
            f"{template.get('name', '')} (копия)"
        )

        if ok and name:
            # Создаём новый шаблон с теми же настройками
            new_template = self.template_manager.create(
                name,
                template.get("settings", {})
            )

            # Обновляем списки
            self._load_templates()
            QMessageBox.information(self, "Успех", f"Шаблон '{name}' создан!")
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
