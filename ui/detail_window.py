# ui/detail_window.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QTextEdit, QPushButton, QMessageBox, QFormLayout
)
from PySide6.QtCore import Qt, Signal
from pathlib import Path
import os
from structurizer.ui.clipboard_utils import copy_file_content_to_clipboard
from structurizer.ui.file_clipboard import copy_file_to_clipboard_as_object

class DetailWindow(QDialog):
    """Окно для просмотра и редактирования деталей анализа"""
    
    item_updated = Signal(dict)  # Сигнал при обновлении элемента
    
    def __init__(self, history_item, history_manager, parent=None):
        super().__init__(parent)
        self.history_item = history_item
        self.history_manager = history_manager
        self.parent = parent
        
        self.setWindowTitle("Детали анализа")
        self.resize(600, 500)
        
        self._build_ui()
        self._load_data()
        
    def _build_ui(self):
        layout = QVBoxLayout(self)
        
        # Форма для редактирования
        form_layout = QFormLayout()
        
        # Название
        self.name_input = QLineEdit()
        form_layout.addRow("Название:", self.name_input)
        
        # Описание
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(100)
        form_layout.addRow("Описание:", self.description_input)
        
        # Информация только для чтения
        self.info_layout = QVBoxLayout()
        
        # Путь к проекту
        self.project_path_label = QLabel()
        self.info_layout.addWidget(QLabel("Путь к проекту:"))
        self.info_layout.addWidget(self.project_path_label)
        
        # Путь к файлу
        self.output_file_label = QLabel()
        self.info_layout.addWidget(QLabel("Файл результата:"))
        self.info_layout.addWidget(self.output_file_label)
        
        # Количество строк
        self.line_count_label = QLabel()
        self.info_layout.addWidget(QLabel("Количество строк:"))
        self.info_layout.addWidget(self.line_count_label)
        
        # Дата создания
        self.date_label = QLabel()
        self.info_layout.addWidget(QLabel("Дата создания:"))
        self.info_layout.addWidget(self.date_label)
        
        layout.addLayout(form_layout)
        layout.addLayout(self.info_layout)
        
        # Кнопки действий
        buttons_layout = QHBoxLayout()
        
        self.save_button = QPushButton("💾 Сохранить")
        self.save_button.clicked.connect(self._save_changes)
        
        self.open_file_button = QPushButton("📄 Открыть файл")
        self.open_file_button.clicked.connect(self._open_file)
        
        self.open_folder_button = QPushButton("📂 Открыть папку")
        self.open_folder_button.clicked.connect(self._open_folder)
        
        self.copy_path_button = QPushButton("📋 Копировать путь")
        self.copy_path_button.clicked.connect(self._copy_path)

        self.copy_file_object_button = QPushButton("📁 Копировать файл")  
        self.copy_file_object_button.clicked.connect(self._copy_file_as_object)

        self.copy_file_button = QPushButton("📋 Копировать содержимое") 
        self.copy_file_button.clicked.connect(self._copy_file_to_clipboard)

        self.delete_button = QPushButton("🗑 Удалить")
        self.delete_button.clicked.connect(self._delete_item)
        
        self.close_button = QPushButton("✕ Закрыть")
        self.close_button.clicked.connect(self.close)
        
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.open_file_button)
        buttons_layout.addWidget(self.open_folder_button)
        buttons_layout.addWidget(self.copy_path_button)
        buttons_layout.addWidget(self.copy_file_object_button)
        buttons_layout.addWidget(self.copy_file_button) 
        buttons_layout.addWidget(self.delete_button)
        buttons_layout.addWidget(self.close_button)
        
        layout.addLayout(buttons_layout)
        
    def _load_data(self):
        """Загружает данные из элемента истории"""
        # Редактируемые поля
        self.name_input.setText(self.history_item.get('display_name', ''))
        self.description_input.setText(self.history_item.get('description', ''))
        
        # Информация только для чтения
        self.project_path_label.setText(self.history_item.get('project_path', ''))
        
        output_file = self.history_item.get('output_file', '')
        self.output_file_label.setText(output_file)
        
        # Подсчет строк в файле
        line_count = self._count_lines(output_file)
        self.line_count_label.setText(str(line_count))
        
        # Форматирование даты
        created_at = self.history_item.get('created_at', '')
        self.date_label.setText(created_at)
        
    def _copy_file_as_object(self):
        """Копирует файл как объект в буфер обмена"""
        output_file = Path(self.history_item.get('output_file', ''))
        if output_file.exists():
            copy_file_to_clipboard_as_object(output_file, self)
        else:
            QMessageBox.warning(self, "Ошибка", "Файл не найден")

    def _copy_file_to_clipboard(self):
        """Копирует содержимое файла в буфер обмена"""
        output_file = Path(self.history_item.get('output_file', ''))
        if output_file.exists():
            copy_file_content_to_clipboard(output_file, self)
        else:
            QMessageBox.warning(self, "Ошибка", "Файл не найден")

    def _count_lines(self, file_path):
        """Подсчитывает количество строк в файле"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return sum(1 for _ in f)
        except:
            return 0
            
    def _save_changes(self):
        """Сохраняет изменения в элементе истории"""
        display_name = self.name_input.text().strip()
        description = self.description_input.toPlainText().strip()
        
        if not display_name:
            QMessageBox.warning(self, "Ошибка", "Название не может быть пустым")
            return
        
        # Обновляем элемент
        updated = self.history_manager.update(
            self.history_item['id'],
            display_name=display_name,
            description=description
        )
        
        if updated:
            # Обновляем локальную копию
            self.history_item.update({
                'display_name': display_name,
                'description': description
            })
            
            # Отправляем сигнал об обновлении
            self.item_updated.emit(self.history_item)
            
            QMessageBox.information(self, "Сохранено", "Изменения сохранены")
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось сохранить изменения")
            
    def _open_file(self):
        """Открывает файл результата"""
        output_file = Path(self.history_item['output_file'])
        if output_file.exists():
            try:
                os.startfile(str(output_file))
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось открыть файл: {e}")
        else:
            QMessageBox.warning(self, "Ошибка", "Файл не найден")
            
    def _open_folder(self):
        """Открывает папку с файлом"""
        output_file = Path(self.history_item['output_file'])
        if output_file.exists():
            try:
                os.system(f'explorer /select,"{output_file}"')
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось открыть папку: {e}")
        else:
            QMessageBox.warning(self, "Ошибка", "Файл не найден")
            
    def _copy_path(self):
        """Копирует путь к файлу в буфер обмена"""
        from PySide6.QtWidgets import QApplication
        from PySide6.QtGui import QClipboard
        
        output_file = Path(self.history_item['output_file'])
        clipboard = QApplication.clipboard()
        clipboard.setText(str(output_file))
        
        QMessageBox.information(self, "Скопировано", "Путь скопирован в буфер обмена")
        
    def _delete_item(self):
        """Удаляет элемент истории"""
        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            "Вы уверены, что хотите удалить этот элемент?\nЭто действие нельзя отменить.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Удаляем через родительское окно
            if self.parent:
                self.parent._delete_history_item_by_id(self.history_item['id'])
            
            # Закрываем окно
            self.reject()