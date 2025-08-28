import os
import shutil
import tempfile
from zipfile import ZipFile

import httpx
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QComboBox,
    QSpinBox,
    QScrollArea,
    QTableView,
    QHeaderView,
    QAbstractItemView,
    QHBoxLayout,
    QMessageBox,
    QLineEdit,
    QFileDialog,
)
from PyQt5.QtGui import QStandardItemModel, QStandardItem

from selecta.logger import generate_logger
from selecta.utils import API_URL

# Logger
logger = generate_logger()


class PlaylistWidget(QWidget):
    def __init__(self, email, playlist_name, songs, songs_df, refresh_callback=None):
        super().__init__()
        self.email = email
        self.playlist_name = playlist_name
        self.songs = songs
        self.songs_df = songs_df
        self.expanded = False
        self.refresh_callback = refresh_callback

        self.layout = QVBoxLayout()
        self.toggle_button = QPushButton(f"▶ {self.playlist_name}")
        self.toggle_button.setCheckable(True)
        self.toggle_button.clicked.connect(self.toggle_content)
        self.layout.addWidget(self.toggle_button)

        # Content widget (initially hidden)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout()

        self.table_view = QTableView()
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["Song Name"])
        for song in songs:
            self.model.appendRow([QStandardItem(song)])

        self.table_view.setModel(self.model)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_view.setSortingEnabled(True)

        self.content_layout.addWidget(self.table_view)

        button_layout = QHBoxLayout()
        self.download_button = QPushButton("Download")
        self.download_button.clicked.connect(self.download_playlist)
        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(lambda: self.delete_playlist(self.playlist_name))
        button_layout.addWidget(self.download_button)
        button_layout.addWidget(self.delete_button)

        self.content_layout.addLayout(button_layout)
        self.content_widget.setLayout(self.content_layout)
        self.content_widget.setVisible(False)
        self.layout.addWidget(self.content_widget)
        self.setLayout(self.layout)

    def toggle_content(self):
        self.expanded = not self.expanded
        self.content_widget.setVisible(self.expanded)
        self.toggle_button.setText(("▼ " if self.expanded else "▶ ") + self.playlist_name)

    def download_playlist(self):
        try:
            # Create a temporary directory to hold the files
            with tempfile.TemporaryDirectory() as temp_dir:
                song_paths = []

                for song_name in self.songs:
                    row = self.songs_df[self.songs_df["name"] == song_name]
                    if not row.empty:
                        song_path = row.iloc[0]["location"]
                        if os.path.isfile(song_path):
                            dest_path = os.path.join(temp_dir, os.path.basename(song_path))
                            shutil.copy2(song_path, dest_path)
                            song_paths.append(dest_path)

                if not song_paths:
                    QMessageBox.warning(None, "Download Failed", "No valid song files found for this playlist.")
                    return

                # Ask user where to save the zip
                zip_file_path, _ = QFileDialog.getSaveFileName(
                    self, "Save Playlist Zip", f"{self.playlist_name}.zip", "Zip Files (*.zip)"
                )
                if not zip_file_path:
                    return

                # Create the zip file
                with ZipFile(zip_file_path, "w") as zipf:
                    for path in song_paths:
                        zipf.write(path, os.path.basename(path))

                QMessageBox.information(None, "Download Complete", f"Playlist zipped and saved to:\n{zip_file_path}")

        except Exception as e:
            logger.error(f"Error downloading playlist: {e}")
            QMessageBox.critical(None, "Error", "An error occurred while creating the playlist zip file.")

    def delete_playlist(self, name):
        # Post to /login endpoint to get access token
        with httpx.Client() as client:
            response = client.post(f"{API_URL}/delete_playlist", json={"email": self.email, "name": name})
            if response.status_code == 200:
                # Update playlists widget
                if self.refresh_callback:
                    self.refresh_callback()
            else:
                error_message = response.json().get("detail", "Failed to delete playlists")
                QMessageBox.warning(None, "Failed to delete playlists", error_message)


class CreatePlaylistDialog(QDialog):
    def __init__(self, song_names):
        super().__init__()
        self.setWindowTitle("Create Playlist")
        self.setMinimumWidth(300)

        layout = QFormLayout(self)

        self.name_input = QLineEdit()
        layout.addRow("Playlist Name:", self.name_input)

        self.root_song_combo = QComboBox()
        self.root_song_combo.setEditable(True)
        self.root_song_combo.addItems(sorted(song_names))
        completer = self.root_song_combo.completer()
        completer.setCaseSensitivity(Qt.CaseInsensitive)

        layout.addRow("Root Song:", self.root_song_combo)

        self.num_songs_spin = QSpinBox()
        self.num_songs_spin.setRange(1, len(song_names) - 1)
        layout.addRow("Number of Songs:", self.num_songs_spin)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addRow(self.buttons)

    def get_values(self):
        return (self.name_input.text(), self.root_song_combo.currentText(), self.num_songs_spin.value())


class PlaylistsPage(QMainWindow):
    def __init__(self, email=None, songs_df=None, similarity_matrix_df=None, access_token=None):
        super().__init__()
        self.setWindowTitle("Playlists")
        self.email = email
        self.access_token = access_token
        self.songs_df = songs_df
        self.similarity_matrix_df = similarity_matrix_df

        self.playlists = []

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.layout = QVBoxLayout(central_widget)

        title = QLabel("Playlists")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.layout.addWidget(title)

        self.create_button = QPushButton("Create New Playlist")
        self.create_button.clicked.connect(self.create_playlist_dialog)
        self.layout.addWidget(self.create_button)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout()
        self.scroll_widget.setLayout(self.scroll_layout)
        self.scroll_area.setWidget(self.scroll_widget)

        self.layout.addWidget(self.scroll_area)

    def get_playlists(self):
        # Post to /login endpoint to get access token
        with httpx.Client() as client:
            response = client.post(f"{API_URL}/read_playlists", json={"email": self.email})
            if response.status_code == 200:
                playlists = response.json()["playlists"]
                self.playlists = playlists
            else:
                error_message = response.json().get("detail", "Failed to get playlists")
                QMessageBox.warning(None, "Failed to get playlists", error_message)

    def refresh(self, songs_df, similarity_matrix_df):
        self.songs_df = songs_df
        self.similarity_matrix_df = similarity_matrix_df
        self.get_playlists()
        self.display_playlists()

    def create_playlist_dialog(self):
        if self.songs_df is None or self.similarity_matrix_df is None:
            QMessageBox.warning(None, "Missing Data", "Songs or similarity matrix not available.")
            return

        dialog = CreatePlaylistDialog(self.songs_df["name"].tolist())
        if dialog.exec_():
            name, root_song, n = dialog.get_values()
            self.generate_playlist(name, root_song, n)

    def generate_playlist(self, name, root_song, n):
        if root_song not in self.similarity_matrix_df.index:
            QMessageBox.warning(None, "Invalid Root Song", "Selected root song not found in similarity matrix.")
            return

        similarities = self.similarity_matrix_df.loc[root_song]
        most_similar = similarities.sort_values(ascending=True, na_position="first")
        most_similar = most_similar[most_similar.index != root_song]
        playlist_songs = most_similar.head(n - 1).index.tolist()
        playlist_songs = [root_song] + playlist_songs

        self.save_playlist(name, playlist_songs)

    def save_playlist(self, name, songs):
        # Post to /login endpoint to get access token
        with httpx.Client() as client:
            response = client.post(
                f"{API_URL}/create_playlist", json={"email": self.email, "name": name, "songs": songs}
            )
            if response.status_code == 200:
                # Update playlists widget
                self.get_playlists()
                self.display_playlists()
            else:
                error_message = response.json().get("detail", "Failed to create playlist")
                QMessageBox.warning(None, "Failed to create playlist", error_message)

    def display_playlists(self):
        # Clear previous widgets
        for i in reversed(range(self.scroll_layout.count())):
            widget_to_remove = self.scroll_layout.itemAt(i).widget()
            if widget_to_remove is not None:
                widget_to_remove.setParent(None)

        # Add updated playlist widgets
        for playlist in self.playlists:
            widget = PlaylistWidget(
                email=self.email,
                playlist_name=playlist["name"],
                songs=playlist["songs"],
                songs_df=self.songs_df,
                refresh_callback=lambda: self.refresh(self.songs_df, self.similarity_matrix_df),
            )
            self.scroll_layout.addWidget(widget)
