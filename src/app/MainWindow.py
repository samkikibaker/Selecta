from PyQt5.QtWidgets import (
    QMainWindow,
    QSplitter,
)
from PyQt5.QtCore import Qt

from selecta.logger import generate_logger
from app.SongsPanel import SongsPanel
from app.PlaylistsPanel import PlaylistsPanel

# Logger
logger = generate_logger()


class MainWindow(QMainWindow):
    def __init__(self, email: str = None, access_token: str = None):
        super().__init__()
        self.setWindowTitle("Selecta")
        self.email = email
        self.access_token = access_token

        # Create SongsPanel and PlaylistsPanel widgets
        self.songs_panel = SongsPanel(email=self.email, access_token=self.access_token)
        self.playlists_panel = PlaylistsPanel(email=self.email, access_token=self.access_token)

        # Use QSplitter for resizable layout
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.songs_panel)
        splitter.addWidget(self.playlists_panel)
        splitter.setSizes([self.width() // 2, self.width() // 2])  # initial equal sizes

        # Set splitter as central widget
        self.setCentralWidget(splitter)
