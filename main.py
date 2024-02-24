import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

from MainWindow import MyMainWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWindow = MyMainWindow()
    mainWindow.setWindowTitle("MultiChannel Signal Viewer")
    mainWindow.setWindowIcon(QIcon("Resources/icons8-ecg-48-2.png"))
    mainWindow.show()
    sys.exit(app.exec())
