import os
import pickle

import httpx
import pandas as pd
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QLabel, QTableView, QHeaderView, QAbstractItemView
from PyQt5.QtGui import QStandardItemModel, QStandardItem

from dotenv import load_dotenv

from selecta.blob_storage import create_blob_container_client, download_blobs
from selecta.logger import generate_logger

# Logger
logger = generate_logger()

# Env vars
load_dotenv()
API_URL = os.getenv("API_URL")


class SongsPage(QMainWindow):
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

        # Login title
        title = QLabel("Songs")
        title.setAlignment(Qt.AlignLeft)
        title.setStyleSheet("font-size: 30px; font-weight: bold;")
        layout.addWidget(title)

        # Table view for songs
        self.table_view = QTableView()
        self.table_model = self.create_table_model(self.songs_df)
        self.table_view.setModel(self.table_model)

        # UI tweaks for nicer table
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_view.setSortingEnabled(True)

        layout.addWidget(self.table_view)

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

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
            songs_df = pd.DataFrame([{"name": song.name, "location": song.path} for song in songs])
        except FileNotFoundError:
            songs_df = pd.DataFrame(columns=["Name", "Location"])
        return songs_df

    def create_table_model(self, df: pd.DataFrame) -> QStandardItemModel:
        model = QStandardItemModel()
        model.setColumnCount(len(df.columns))
        model.setHorizontalHeaderLabels(df.columns.tolist())

        for row in df.itertuples(index=False):
            items = [QStandardItem(str(field)) for field in row]
            model.appendRow(items)

        return model
