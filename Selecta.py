import sys
import multiprocessing

from PyQt5.QtWidgets import QApplication
from app.MainWindow import MainWindow
from selecta.logger import generate_logger

multiprocessing.freeze_support()
multiprocessing.set_start_method("spawn", force=True)

logger = generate_logger()


def run_app():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    try:
        run_app()
    except Exception as e:
        logger.error(e)
