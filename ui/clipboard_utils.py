from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QClipboard
from pathlib import Path

def copy_file_content_to_clipboard(file_path, parent_widget=None, max_file_size_mb=10):
    """
    Копирует содержимое файла в буфер обмена.
    
    Args:
        file_path: путь к файлу
        parent_widget: родительское окно для диалоговых окон
        max_file_size_mb: максимальный размер файла в МБ для копирования без предупреждения
    """
    file_path = Path(file_path)
    
    # Проверяем существование файла
    if not file_path.exists():
        QMessageBox.warning(
            parent_widget, 
            "Файл не найден", 
            f"Файл не существует:\n{file_path}"
        )
        return False
    
    # Проверяем размер файла
    file_size_mb = file_path.stat().st_size / (1024 * 1024)
    
    if file_size_mb > max_file_size_mb:
        reply = QMessageBox.question(
            parent_widget,
            "Большой файл",
            f"Файл имеет размер {file_size_mb:.1f} МБ.\n"
            f"Копирование может занять некоторое время.\n"
            "Вы хотите продолжить?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return False
    
    try:
        # Читаем содержимое файла
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Копируем в буфер обмена
        clipboard = QApplication.clipboard()
        clipboard.setText(content)
        
        # Показываем сообщение об успехе
        QMessageBox.information(
            parent_widget,
            "Успешно",
            f"Содержимое файла скопировано в буфер обмена.\n"
            f"Размер: {len(content):,} символов"
        )
        return True
        
    except UnicodeDecodeError:
        QMessageBox.warning(
            parent_widget,
            "Ошибка чтения",
            "Файл не является текстовым в кодировке UTF-8."
        )
        return False
        
    except Exception as e:
        QMessageBox.critical(
            parent_widget,
            "Ошибка",
            f"Не удалось скопировать файл:\n{str(e)}"
        )
        return False