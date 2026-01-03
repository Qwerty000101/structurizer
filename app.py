import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from structurizer.ui.main_window import MainWindow

def main():
    # Устанавливаем переменные окружения для Qt
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Более современный стиль
    
    # Устанавливаем иконку приложения
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Пробуем разные пути к иконке
    icon_paths = [
        os.path.join(base_dir, "icon.ico"),
        os.path.join(base_dir, "ui", "icons", "icon.ico"),
        os.path.join(base_dir, "ui", "icons", "app_icon.ico"),
        os.path.join(base_dir, "icon.png"),
    ]
    
    for icon_path in icon_paths:
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
            print(f"Иконка загружена: {icon_path}")
            break
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()