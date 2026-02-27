import pickle

import pandas as pd

from pathlib import Path
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

from app.AnalysisWorker import AnalysisWorker
from selecta.utils import get_similarity_matrix_cache, get_songs_cache, get_local_app_data_dir, get_playlists_cache


class SongsPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.songs, self.songs_df = get_songs_cache()
        self.similarity_matrix_df = get_similarity_matrix_cache()
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
        delete_songs_button = QPushButton("Delete Songs")
        add_songs_button.clicked.connect(self.select_folder)
        analyse_songs_button.clicked.connect(self.analyse_songs)
        delete_songs_button.clicked.connect(self.delete_selected_songs)
        button_layout.addWidget(add_songs_button)
        button_layout.addWidget(analyse_songs_button)
        button_layout.addWidget(delete_songs_button)
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

            # Filter to songs not yet added
            subset_cols = ["name", "location"]
            self.new_songs_df = self.added_songs_df[
                ~self.added_songs_df[subset_cols].isin(self.songs_df[subset_cols]).all(axis=1)
            ]

            # Update the main table model with all songs
            self.table_model = self.create_table_model(pd.concat([self.songs_df, self.added_songs_df]))
            self.table_view.setModel(self.table_model)

            QMessageBox.information(
                None,
                "Added Songs",
                f"Added {len(self.new_songs_df)} new songs. Total songs: {len(self.new_songs_df) + len(self.songs_df)}",
            )

    def analyse_songs(self):
        if self.new_songs_df.empty:
            QMessageBox.warning(None, "No Songs", "Please add new songs before analysing.")
            return

        worker = AnalysisWorker(new_songs_df=self.new_songs_df)

        # Connect signals to slots
        worker.signals.status.connect(self.update_status)
        worker.signals.analysis_progress.connect(self.update_analysis_progress)
        worker.signals.similarity_progress.connect(self.update_similarity_progress)

        self.threadpool.start(worker)

        self.refresh()

    def update_status(self, message: str):
        self.status_label.setText(message)

    def update_analysis_progress(self, value: int):
        self.analysis_progress_bar.setValue(value)

    def update_similarity_progress(self, value: int):
        self.similarity_progress_bar.setValue(value)

    def delete_selected_songs(self):
        self.refresh()

        selection_model = self.table_view.selectionModel()
        selected_rows = selection_model.selectedRows()  # returns QModelIndex list

        if not selected_rows:
            return  # Nothing selected

        # Extract song names from the selected rows
        song_names_to_delete = []
        for index in selected_rows:
            row = index.row()
            song_name = self.songs_df.iloc[row]["name"]
            song_names_to_delete.append(song_name)

        # Call your existing function
        self.delete_songs(song_names_to_delete)

        # Update the table view to reflect changes
        self.refresh()

        self.table_model = self.create_table_model(self.songs_df)
        self.table_view.setModel(self.table_model)

    def delete_songs(self, song_names):
        local_app_data_dir = get_local_app_data_dir()
        songs_cache, _ = get_songs_cache()
        similarity_matrix_cache = get_similarity_matrix_cache()
        playlists_cache = get_playlists_cache()

        # Filter songs and save back to cache
        songs_cache_updated = [song for song in songs_cache if song.name not in song_names]
        songs_cache_path = Path(f"{local_app_data_dir}/cache/songs.pickle")
        with open(songs_cache_path, "wb") as f:
            pickle.dump(songs_cache_updated, f)

        # Filter similarity matrix cols and index and save back to cache
        similarity_matrix_cache_updated = similarity_matrix_cache[[col for col in similarity_matrix_cache.columns if col not in song_names]]
        similarity_matrix_cache_updated = similarity_matrix_cache_updated[~similarity_matrix_cache_updated.index.isin(song_names)]
        similarity_matrix_cache_path = Path(f"{local_app_data_dir}/cache/similarity_matrix.pickle")
        with open(similarity_matrix_cache_path, "wb") as f:
            pickle.dump(similarity_matrix_cache_updated, f)

        # Filter playlists and save back to cache
        playlists_cache_updated = playlists_cache.copy()
        playlists_cache["songs"] = playlists_cache["songs"].apply(lambda x: [song_name for song_name in x if song_name not in song_names])
        playlists_cache_path = Path(f"{local_app_data_dir}/cache/playlists.pickle")
        with open(playlists_cache_path, "wb") as f:
            pickle.dump(playlists_cache_updated, f)

    def refresh(self):
        self.songs, self.songs_df = get_songs_cache()
        self.similarity_matrix_df = get_similarity_matrix_cache()
