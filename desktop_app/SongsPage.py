import os
import pickle

import httpx
import pandas as pd
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QLabel,
    QTableView,
    QHeaderView,
    QAbstractItemView,
    QPushButton,
    QFileDialog,
)
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from pathlib import Path
from dotenv import load_dotenv

from selecta.blob_storage import create_blob_container_client, download_blobs
from selecta.logger import generate_logger

# Logger
logger = generate_logger()

# Env vars
load_dotenv()
API_URL = os.getenv("API_URL")


class SongsPage(QMainWindow):
    def __init__(self, email: str = None, songs_df: pd.DataFrame = None, access_token: str = None):
        super().__init__()
        self.setWindowTitle("Selecta")
        self.email = email
        self.songs_df = songs_df
        self.access_token = access_token

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
        layout.addWidget(self.table_view)

        # UI tweaks for nicer table
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_view.setSortingEnabled(True)

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def create_table_model(self, df: pd.DataFrame) -> QStandardItemModel:
        model = QStandardItemModel()
        model.setColumnCount(len(df.columns))
        model.setHorizontalHeaderLabels(df.columns.tolist())

        for row in df.itertuples(index=False):
            items = [QStandardItem(str(field)) for field in row]
            model.appendRow(items)

        return model

    def refresh(self, songs_df, similarity_matrix_df):
        self.songs_df = songs_df
        self.similarity_matrix_df = similarity_matrix_df

        # Rebuild and apply new table model
        self.table_model = self.create_table_model(self.songs_df)
        self.table_view.setModel(self.table_model)
