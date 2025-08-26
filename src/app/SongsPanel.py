from pathlib import Path

import pandas as pd

from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt, QThreadPool
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QTableView,
    QHeaderView,
    QAbstractItemView,
    QHBoxLayout,
    QPushButton,
    QProgressBar,
    QMessageBox,
    QFileDialog,
)

from desktop_app.AnalysisWorker import AnalysisWorker


class SongsPanel(QWidget):
    def __init__(self, email: str = None, access_token: str = None, songs_df=None, similarity_matrix_df=None):
        super().__init__()
        self.email = email
        self.access_token = access_token
        self.songs_df = songs_df
        self.similarity_matrix_df = similarity_matrix_df
        self.added_songs_df = pd.DataFrame()
        self.new_songs_df = pd.DataFrame()

        layout = QVBoxLayout()  # Main vertical layout
        self.panel_header = QHBoxLayout()  # Header with 3 vertical columns

        # Threadpool for background workers
        self.threadpool = QThreadPool()

        # --- Column 1: Title ---
        title_layout = QVBoxLayout()
        title = QLabel("Songs")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 48px; font-weight: bold; margin-bottom: 16px;")
        title_layout.addWidget(title)
        self.panel_header.addLayout(title_layout)

        # --- Column 2: Status + Progress Bars ---
        progress_layout = QVBoxLayout()
        self.status_label = QLabel("")
        self.analysis_progress_bar = QProgressBar()
        self.analysis_progress_bar.setRange(0, 100)
        self.analysis_progress_bar.setValue(0)

        self.similarity_progress_bar = QProgressBar()
        self.similarity_progress_bar.setRange(0, 100)
        self.similarity_progress_bar.setValue(0)

        progress_layout.addWidget(self.status_label)
        progress_layout.addWidget(self.analysis_progress_bar)
        progress_layout.addWidget(self.similarity_progress_bar)
        self.panel_header.addLayout(progress_layout)

        # --- Column 3: Buttons ---
        button_layout = QVBoxLayout()
        add_songs_button = QPushButton("Add Songs")
        analyse_songs_button = QPushButton("Analyse Songs")
        add_songs_button.clicked.connect(self.select_folder)
        analyse_songs_button.clicked.connect(self.analyse_songs)
        button_layout.addWidget(add_songs_button)
        button_layout.addWidget(analyse_songs_button)
        self.panel_header.addLayout(button_layout)

        # --- Table View ---
        self.table_view = QTableView()
        self.table_model = self.create_table_model(self.songs_df)
        self.table_view.setModel(self.table_model)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_view.setSortingEnabled(True)

        # --- Assemble the layout ---
        layout.addLayout(self.panel_header)
        layout.addWidget(self.table_view)
        self.setLayout(layout)

    @staticmethod
    def create_table_model(df: pd.DataFrame) -> QStandardItemModel:
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
                added_songs.append({"name": file_path.name, "location": file_path})
            self.added_songs_df = pd.DataFrame(added_songs)
            self.new_songs_df = pd.concat([self.added_songs_df, self.songs_df, self.songs_df]).drop_duplicates(
                keep=False
            )

            self.table_model = self.create_table_model(self.new_songs_df)
            self.table_view.setModel(self.table_model)

            QMessageBox.information(self, "Added Songs", f"Added {len(self.new_songs_df)} songs not already analysed")

    def analyse_songs(self):
        if self.new_songs_df.empty:
            QMessageBox.warning(self, "No Songs", "Please add new songs before analysing.")
            return

        worker = AnalysisWorker(new_songs_df=self.new_songs_df, email=self.email)

        # Reset progress bars
        self.analysis_progress_bar.setValue(0)
        self.similarity_progress_bar.setValue(0)

        # Connect signals to slots
        worker.signals.status.connect(self.update_status)
        worker.signals.analysis_progress.connect(self.update_analysis_progress)
        worker.signals.similarity_progress.connect(self.update_similarity_progress)

        self.threadpool.start(worker)

    def update_status(self, message: str):
        self.status_label.setText(message)

    def update_analysis_progress(self, value: int):
        self.analysis_progress_bar.setValue(value)

    def update_similarity_progress(self, value: int):
        self.similarity_progress_bar.setValue(value)

    def refresh(self, songs_df, similarity_matrix_df):
        self.songs_df = songs_df
        self.similarity_matrix_df = similarity_matrix_df

        self.new_songs_df = pd.concat([self.added_songs_df, self.songs_df, self.songs_df]).drop_duplicates(keep=False)

        self.table_model = self.create_table_model(self.new_songs_df)
        self.table_view.setModel(self.table_model)
