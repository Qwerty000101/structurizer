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
from PySide6.QtCore import Qt
from structurizer.storage.history_manager import HistoryManager
from pathlib import Path

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Project Analyzer")
        self.resize(1100, 700)

        BASE_DIR = Path(__file__).resolve().parent.parent

        self.history_manager = HistoryManager(
            base_dir=BASE_DIR / "storage"  # ← убрать / "outputs"
        )
        self._build_ui()
        self._load_history()

    def _load_history(self):
        self.history_list.clear()
        items = self.history_manager.load()
        for entry in items:
            item_text = entry["project_path"]  # ← исправлено с "path" на "project_path"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, entry)  # сохраняем весь словарь
            self.history_list.addItem(item)


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

    # =====================
    # Заглушки обработчиков
    # =====================
    def _on_history_item_clicked(self, item):
        entry = item.data(Qt.UserRole)

        output_file = entry["output_file"]
        print("Выбран файл:", output_file)

    def _on_browse_clicked(self):
        QFileDialog.getExistingDirectory(self, "Выбор папки")

    def _on_history_context_menu(self, pos):
        item = self.history_list.itemAt(pos)
        if not item:
            return

        entry = item.data(Qt.UserRole)
        print("Контекстное меню для:", entry["path"])
