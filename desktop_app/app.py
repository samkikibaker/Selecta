import sys
from PyQt5.QtWidgets import QApplication
from desktop_app.LoginWindow import LoginWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    app.exec()
