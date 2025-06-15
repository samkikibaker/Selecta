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
from dotenv import load_dotenv

from desktop_app.PlaylistsPage import PlaylistsPage
from desktop_app.SongsPage import SongsPage
from desktop_app.AnalysePage import AnalysePage
from selecta.blob_storage import create_blob_container_client, download_blobs
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
        self.blob_container_client = create_blob_container_client(
            storage_account="saselecta", container="containerselecta"
        )
        self.songs_df = self.get_songs_cache()

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

    def display_page(self, index):
        self.stack.setCurrentIndex(index)
        self.menu.setCurrentRow(index)

    def get_songs_cache(self):
        download_blobs(
            container_client=self.blob_container_client,
            prefix=f"users/{self.email}/cache/songs.pickle",
            local_dir_path=f"../cache/",
        )
        try:
            with open(f"../cache/songs.pickle", "rb") as f:
                songs = pickle.load(f)
            os.remove("../cache/songs.pickle")
            songs_df = pd.DataFrame(
                [{"name": song.name.lower(), "location": song.path} for song in songs]
            )
        except FileNotFoundError:
            songs_df = pd.DataFrame(columns=["Name", "Location"])
        return songs_df

    def get_similarity_matrix_cache(self):

        download_blobs(
            container_client=self.blob_container_client,
            prefix=f"users/{self.email}/cache/similarity_matrix.pickle",
            local_dir_path=f"../cache/",
        )
        try:
            with open(f"../cache/similarity_matrix.pickle", "rb") as f:
                songs = pickle.load(f)
            os.remove("../cache/similarity_matrix.pickle")
            songs_df = pd.DataFrame(
                [{"name": song.name.lower(), "location": song.path} for song in songs]
            )
        except FileNotFoundError:
            songs_df = pd.DataFrame(columns=["Name", "Location"])
        return songs_df