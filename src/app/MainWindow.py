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
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Selecta")

        # Create SongsPanel and PlaylistsPanel widgets
        self.songs_panel = SongsPanel()
        self.playlists_panel = PlaylistsPanel()

        # Use QSplitter for resizable layout
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.songs_panel)
        splitter.addWidget(self.playlists_panel)
        splitter.setSizes([self.width() // 2, self.width() // 2])  # initial equal sizes

        # Set splitter as central widget
        self.setCentralWidget(splitter)
