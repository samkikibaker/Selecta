import os

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
    QFileDialog, QMessageBox,
)
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from pathlib import Path
from dotenv import load_dotenv

from selecta.logger import generate_logger

# Logger
logger = generate_logger()

# Env vars
load_dotenv()
API_URL = os.getenv("API_URL")


class AnalysePage(QMainWindow):
    def __init__(self, email: str = None, songs_df: pd.DataFrame = None, access_token: str = None):
        super().__init__()
        self.setWindowTitle("Selecta")
        self.email = email
        self.access_token = access_token
        self.songs_df = songs_df
        self.added_songs_df = pd.DataFrame()
        self.new_songs_df = pd.DataFrame()

        # Create the central widget and layout
        central_widget = QWidget()
        layout = QHBoxLayout()

        # Login title
        title = QLabel("Analyse")
        title.setAlignment(Qt.AlignLeft)
        title.setStyleSheet("font-size: 30px; font-weight: bold;")
        layout.addWidget(title)

        # Add songs button
        add_songs_button = QPushButton("Add Songs")
        add_songs_button.clicked.connect(self.select_folder)
        layout.addWidget(add_songs_button)

        # Table view for songs
        self.table_view = QTableView()
        self.table_model = self.create_table_model(self.new_songs_df)
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

    def select_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            added_songs = []
            audio_files = list(Path(folder_path).rglob("*.mp3"))
            for file_path in audio_files:
                added_songs.append(
                    {"name": file_path.name.lower(), "location": file_path}
                )
            self.added_songs_df = pd.DataFrame(added_songs)
            # Any row found in both will appear 3 times
            # Any row found only in songs_df will appear twice
            # Any row found only in added_songs_df with appear once
            # So this filters to just the new songs
            self.new_songs_df = pd.concat([self.added_songs_df, self.songs_df, self.songs_df]).drop_duplicates(keep=False)

            self.table_model = self.create_table_model(self.new_songs_df)
            self.table_view.setModel(self.table_model)

            QMessageBox.information(self, "Added Songs", f"Added {len(self.new_songs_df)} songs not already analysed")
