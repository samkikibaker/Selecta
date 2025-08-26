import pickle

import pandas as pd
from PyQt5.QtWidgets import (
    QMainWindow,
    QSplitter,
)
from PyQt5.QtCore import Qt
from pathlib import Path

from selecta.logger import generate_logger
from app.SongsPanel import SongsPanel
from app.PlaylistsPanel import PlaylistsPanel
from selecta.utils import local_app_data_dir

# Logger
logger = generate_logger()


class MainWindow(QMainWindow):
    def __init__(self, email: str = None, access_token: str = None):
        super().__init__()
        self.setWindowTitle("Selecta")
        self.email = email
        self.access_token = access_token
        self.songs_df = self.get_songs_cache()
        self.similarity_matrix_df = self.get_similarity_matrix_cache()

        # Create SongsPanel and PlaylistsPanel widgets
        self.songs_panel = SongsPanel(
            email=self.email,
            songs_df=self.songs_df,
            similarity_matrix_df=self.similarity_matrix_df,
            access_token=self.access_token
        )
        self.playlists_panel = PlaylistsPanel(
            email=self.email,
            songs_df=self.songs_df,
            similarity_matrix_df=self.similarity_matrix_df,
            access_token=self.access_token
        )

        # Use QSplitter for resizable layout
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.songs_panel)
        splitter.addWidget(self.playlists_panel)
        splitter.setSizes([self.width() // 2, self.width() // 2])  # initial equal sizes

        # Set splitter as central widget
        self.setCentralWidget(splitter)

    @staticmethod
    def get_songs_cache():
        local_path = Path(f"{local_app_data_dir}/cache/songs.pickle")
        try:
            with open(local_path, "rb") as f:
                songs = pickle.load(f)
            songs_df = pd.DataFrame([{"name": song.name, "location": song.path} for song in songs])
        except FileNotFoundError:
            songs_df = pd.DataFrame(columns=["name", "location"])
        return songs_df

    @staticmethod
    def get_similarity_matrix_cache():
        local_path = Path(f"{local_app_data_dir}/cache/similarity_matrix.pickle")
        try:
            with open(local_path, "rb") as f:
                similarity_matrix_df = pickle.load(f)
        except FileNotFoundError:
            similarity_matrix_df = pd.DataFrame()
        return similarity_matrix_df
