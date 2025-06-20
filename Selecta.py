import sys
from PyQt5.QtWidgets import QApplication
from desktop_app.LoginWindow import LoginWindow
from selecta.logger import generate_logger

logger = generate_logger()


def run_app():
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    import multiprocessing

    multiprocessing.freeze_support()
    multiprocessing.set_start_method("spawn", force=True)

    try:
        run_app()
    except Exception as e:
        logger.error(e)
