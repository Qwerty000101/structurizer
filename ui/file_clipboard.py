# ui/file_clipboard.py

import os
import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt, QMimeData, QUrl
from PySide6.QtGui import QClipboard

def copy_file_to_clipboard_as_object(file_path, parent_widget=None):
    """
    Копирует файл в буфер обмена как объект файла.
    Позволяет вставлять файл в проводник и другие приложения.
    
    Args:
        file_path: путь к файлу
        parent_widget: родительское окно для диалоговых окон
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
    
    try:
        # Получаем буфер обмена
        clipboard = QApplication.clipboard()
        
        # Создаем QMimeData для передачи файла
        mime_data = QMimeData()
        
        # Создаем URL для файла
        url = QUrl.fromLocalFile(str(file_path))
        
        # Устанавливаем URL в формате text/uri-list (стандарт для передачи файлов)
        mime_data.setUrls([url])
        
        # Также устанавливаем данные в других форматах для совместимости
        mime_data.setText(str(file_path))
        mime_data.setData("FileName", str(file_path.name).encode('utf-8'))
        mime_data.setData("FileNameW", str(file_path.name).encode('utf-16-le'))
        
        # Для Windows: устанавливаем данные в формате CF_HDROP
        if sys.platform == 'win32':
            # Создаем строку в формате, который ожидает Windows для DROPFILES
            import ctypes
            from ctypes import wintypes
            
            # Формируем строку с нулевым окончанием
            file_str = str(file_path.resolve()) + '\0'
            
            # Создаем структуру DROPFILES
            class DROPFILES(ctypes.Structure):
                _fields_ = [
                    ("pFiles", wintypes.DWORD),
                    ("pt", wintypes.POINT),
                    ("fNC", wintypes.BOOL),
                    ("fWide", wintypes.BOOL),
                ]
            
            # Вычисляем размер данных
            data_size = ctypes.sizeof(DROPFILES) + len(file_str.encode('utf-16-le')) + 2
            
            # Создаем буфер
            data = ctypes.create_string_buffer(data_size)
            
            # Заполняем структуру
            dropfiles = DROPFILES.from_buffer(data)
            dropfiles.pFiles = ctypes.sizeof(DROPFILES)
            dropfiles.fWide = True
            
            # Копируем строку файла
            file_bytes = file_str.encode('utf-16-le')
            ctypes.memmove(
                ctypes.addressof(data) + ctypes.sizeof(DROPFILES),
                file_bytes,
                len(file_bytes)
            )
            
            # Добавляем двойной нуль в конец
            data[data_size-2:data_size] = b'\0\0'
            
            # Устанавливаем данные в формате CF_HDROP
            mime_data.setData("application/x-qt-windows-mime;value=\"HDROP\"", 
                            bytes(data))
        
        # Устанавливаем MIME-данные в буфер обмена
        clipboard.setMimeData(mime_data)
        
        # Показываем сообщение об успехе
        QMessageBox.information(
            parent_widget,
            "Файл скопирован",
            f"Файл '{file_path.name}' скопирован в буфер обмена."
        )
        return True
        
    except Exception as e:
        QMessageBox.critical(
            parent_widget,
            "Ошибка",
            f"Не удалось скопировать файл:\n{str(e)}"
        )
        return False