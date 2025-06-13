import os

from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QListWidget,
    QStackedWidget,
)
from dotenv import load_dotenv

from desktop_app.PlaylistsPage import PlaylistsPage
from desktop_app.SongsPage import SongsPage
from selecta.logger import generate_logger

# Logger
logger = generate_logger()

# Env vars
load_dotenv()
API_URL = os.getenv("API_URL")


class MainWindow(QMainWindow):
    def __init__(self, email: str = None, access_token: str = None):
        super().__init__()
        self.setWindowTitle("Selecta")
        self.email = email
        self.access_token = access_token

        # Create the central widget and layout
        central_widget = QWidget()
        layout = QHBoxLayout()

        # Sidebar menu
        self.menu = QListWidget()
        self.menu.addItems(["Songs", "Playlists"])
        self.menu.currentRowChanged.connect(self.display_page)
        layout.addWidget(self.menu)

        # Main content
        self.stack = QStackedWidget()
        self.stack.addWidget(SongsPage(email=self.email, access_token=self.access_token))
        self.stack.addWidget(PlaylistsPage(email=self.email, access_token=self.access_token))
        layout.addWidget(self.stack)

        # Sidebar should only take a fraction of the width
        layout.setStretch(0, 1)  # Sidebar
        layout.setStretch(1, 4)  # Main content

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def display_page(self, index):
        self.stack.setCurrentIndex(index)
        self.menu.setCurrentRow(index)
