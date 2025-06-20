import os
import pickle

import pandas as pd
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QListWidget,
    QStackedWidget,
)
from pathlib import Path

from desktop_app.PlaylistsPage import PlaylistsPage
from desktop_app.SongsPage import SongsPage
from desktop_app.AnalysePage import AnalysePage
from selecta.logger import generate_logger

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

        # Create the central widget and layout
        central_widget = QWidget()
        layout = QHBoxLayout()

        # Sidebar menu
        self.menu = QListWidget()
        self.menu.addItems(["Songs", "Analyse", "Playlists"])
        self.menu.currentRowChanged.connect(self.display_page)
        layout.addWidget(self.menu)

        # Main content
        self.stack = QStackedWidget()
        self.stack.addWidget(SongsPage(email=self.email, songs_df=self.songs_df, access_token=self.access_token))
        self.stack.addWidget(AnalysePage(email=self.email, songs_df=self.songs_df, access_token=self.access_token))
        self.stack.addWidget(PlaylistsPage(email=self.email, songs_df=self.songs_df, access_token=self.access_token))
        layout.addWidget(self.stack)

        # Sidebar should only take a fraction of the width
        layout.setStretch(0, 1)  # Sidebar
        layout.setStretch(1, 4)  # Main content

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def refresh_data(self):
        self.songs_df = self.get_songs_cache()
        self.similarity_matrix_df = self.get_similarity_matrix_cache()

        # Refresh each page with new data
        self.stack.widget(0).refresh(self.songs_df, self.similarity_matrix_df)
        self.stack.widget(1).refresh(self.songs_df, self.similarity_matrix_df)
        self.stack.widget(2).refresh(self.songs_df, self.similarity_matrix_df)

    def display_page(self, index):
        self.songs_df = self.get_songs_cache()
        self.similarity_matrix_df = self.get_similarity_matrix_cache()

        page = self.stack.widget(index)
        if hasattr(page, "refresh"):
            page.refresh(self.songs_df, self.similarity_matrix_df)

        self.stack.setCurrentIndex(index)
        self.menu.setCurrentRow(index)

    def get_songs_cache(self):
        local_path = Path("~/Library/Application Support/Selecta/cache/songs.pickle")
        try:
            with open(local_path, "rb") as f:
                songs = pickle.load(f)
            songs_df = pd.DataFrame([{"name": song.name, "location": song.path} for song in songs])
        except FileNotFoundError:
            songs_df = pd.DataFrame(columns=["Name", "Location"])
        return songs_df

    def get_similarity_matrix_cache(self):
        local_path = Path("~/Library/Application Support/Selecta/cache/similarity_matrix.pickle")
        try:
            with open(local_path, "rb") as f:
                similarity_matrix_df = pickle.load(f)
        except FileNotFoundError:
            similarity_matrix_df = pd.DataFrame()
        return similarity_matrix_df
