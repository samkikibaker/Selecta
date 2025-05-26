import sys
import asyncio
import os
import pickle
import json
import pandas as pd
import httpx

from dotenv import load_dotenv
from PyQt5.QtWidgets import ( QApplication, QWidget, QVBoxLayout, QPushButton, QLineEdit, QLabel, QTabWidget,
                              QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem,
)
from PyQt5.QtCore import Qt, QRunnable, QThreadPool
from pathlib import Path

from selecta.SongProcessorDesktop import SongProcessorDesktop
from selecta.Song import Song
from selecta.blob_storage import download_blobs, create_blob_container_client

load_dotenv()
API_URL = os.getenv("API_URL")


class SongAnalysisWorker(QRunnable):
    def __init__(self, email, song_table):
        super().__init__()
        self.song_table = song_table
        self.email = email

    def run(self):
        song_paths = [Path(self.song_table.item(row, 1).text()) for row in range(self.song_table.rowCount())]
        song_processor_desktop = SongProcessorDesktop(email=self.email, local_song_paths=song_paths)


class SelectaApp(QWidget):
    def __init__(self):
        super().__init__()
        self.email = None
        self.access_token = None
        self.song_table = None
        self.container_client = create_blob_container_client(storage_account="saselecta", container="containerselecta")
        self.similarity_matrix = self.get_similarity_matrix()

        self.setWindowTitle("Selecta")

        self.layout = QVBoxLayout()
        self.tabs = QTabWidget()

        self.login_tab = QWidget()
        self.register_tab = QWidget()
        self.tabs.addTab(self.login_tab, "Login")
        self.tabs.addTab(self.register_tab, "Register")

        self.main_widget = QWidget()

        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)

        self.init_login_tab()
        self.init_register_tab()
        self.init_main_widget()

    def init_login_tab(self):
        login_layout = QVBoxLayout()
        login_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        login_layout.setContentsMargins(40, 60, 40, 40)
        login_layout.setSpacing(20)

        # Email Label + Field
        email_label = QLabel("Email:")
        self.login_email = QLineEdit()
        self.login_email.setPlaceholderText("Enter your email")
        self.login_email.setFixedWidth(300)

        # Group email label and field
        email_layout = QVBoxLayout()
        email_layout.addWidget(email_label)
        email_layout.addWidget(self.login_email)

        # Password Label + Field
        password_label = QLabel("Password:")
        self.login_password = QLineEdit()
        self.login_password.setPlaceholderText("Enter your password")
        self.login_password.setEchoMode(QLineEdit.Password)
        self.login_password.setFixedWidth(300)

        password_layout = QVBoxLayout()
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.login_password)

        # Login button
        login_button = QPushButton("Login")
        login_button.setFixedWidth(150)
        login_button.clicked.connect(self.login)

        # Add all groups to layout
        login_layout.addLayout(email_layout)
        login_layout.addLayout(password_layout)
        login_layout.addWidget(login_button, alignment=Qt.AlignCenter)

        self.login_tab.setLayout(login_layout)

    def init_register_tab(self):
        register_layout = QVBoxLayout()
        register_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        register_layout.setContentsMargins(40, 60, 40, 40)
        register_layout.setSpacing(20)

        # Email field
        email_label = QLabel("Email:")
        self.register_email = QLineEdit()
        self.register_email.setPlaceholderText("Enter your email")
        self.register_email.setFixedWidth(300)

        # Password field
        password_label = QLabel("Password:")
        self.register_password = QLineEdit()
        self.register_password.setPlaceholderText("Enter your password")
        self.register_password.setEchoMode(QLineEdit.Password)
        self.register_password.setFixedWidth(300)

        # Confirm password field
        confirm_label = QLabel("Confirm Password:")
        self.register_confirm_password = QLineEdit()
        self.register_confirm_password.setPlaceholderText("Confirm your password")
        self.register_confirm_password.setEchoMode(QLineEdit.Password)
        self.register_confirm_password.setFixedWidth(300)

        # Register button
        register_button = QPushButton("Register")
        register_button.setFixedWidth(150)
        register_button.clicked.connect(self.register)

        # Add widgets to layout
        register_layout.addWidget(email_label)
        register_layout.addWidget(self.register_email)
        register_layout.addWidget(password_label)
        register_layout.addWidget(self.register_password)
        register_layout.addWidget(confirm_label)
        register_layout.addWidget(self.register_confirm_password)
        register_layout.addWidget(register_button, alignment=Qt.AlignCenter)

        self.register_tab.setLayout(register_layout)

    def init_main_widget(self):
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        main_layout.setContentsMargins(40, 60, 40, 40)
        main_layout.setSpacing(20)

        # Add button to select folder or file
        import_button = QPushButton("Import Songs")
        import_button.setFixedWidth(200)
        import_button.clicked.connect(self.import_songs)
        main_layout.addWidget(import_button, alignment=Qt.AlignCenter)

        # Add button to start the analysis job
        analyse_button = QPushButton("Analyse Songs")
        analyse_button.setFixedWidth(200)
        analyse_button.clicked.connect(self.analyse_songs)
        main_layout.addWidget(analyse_button, alignment=Qt.AlignCenter)

        # Add song table
        self.song_table = QTableWidget()
        self.song_table.setColumnCount(2)
        self.song_table.setHorizontalHeaderLabels(["Name", "Location"])
        self.song_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.song_table.setColumnWidth(0, 300)
        self.song_table.setColumnWidth(1, 600)
        main_layout.addWidget(self.song_table)

        self.main_widget.setLayout(main_layout)

    def login(self):
        email = self.login_email.text()
        password = self.login_password.text()
        if email and password:
            response = asyncio.run(self.api_post("login", {"email": email, "password": password}))
            if response.status_code == 200:
                self.access_token = response.json()["access_token"]
                self.email = email
                self.layout.removeWidget(self.tabs)
                self.tabs.setParent(None)
                self.layout.addWidget(self.main_widget)
                # self.refresh_playlists()
            else:
                QMessageBox.warning(self, "Error", "Login failed.")

    def register(self):
        email = self.register_email.text()
        password = self.register_password.text()
        confirm_password = self.register_confirm_password.text()

        if password != confirm_password:
            QMessageBox.warning(self, "Error", "Passwords do not match.")
            return

        if email and password:
            response = asyncio.run(self.api_post("register", {"email": email, "password": password}))
            if response.status_code == 200:
                QMessageBox.information(self, "Success", "Registered successfully!")
            else:
                QMessageBox.warning(self, "Error", f"Registration failed: {response.text}")

    def import_songs(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if not folder_path:
            return

        paths = list(Path(folder_path).rglob("*.mp3"))

        for path in paths:
            if not any(self.song_table.item(row, 1).text() == str(path) for row in range(self.song_table.rowCount())):
                row = self.song_table.rowCount()
                self.song_table.insertRow(row)
                self.song_table.setItem(row, 0, QTableWidgetItem(path.name))
                self.song_table.setItem(row, 1, QTableWidgetItem(str(path)))

        # Sort by name column (0), ascending order
        self.song_table.sortItems(0, Qt.AscendingOrder)

    def analyse_songs(self):
        worker = SongAnalysisWorker(email=self.email, song_table=self.song_table)
        QThreadPool.globalInstance().start(worker)

    def get_similarity_matrix(self):
        download_blobs(
            container_client=self.container_client,
            prefix=f"users/{self.email}/cache/similarity_matrix.pickle",
            local_dir_path=f"cache/",
        )
        try:
            with open(f"cache/similarity_matrix.pickle", "rb") as f:
                similarity_matrix = pickle.load(f)
        except FileNotFoundError:
            similarity_matrix = pd.DataFrame()
        return similarity_matrix

    @staticmethod
    async def api_post(endpoint, json_data):
        async with httpx.AsyncClient() as client:
            return await client.post(f"{API_URL}/{endpoint}", json=json_data)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SelectaApp()
    window.showFullScreen()
    sys.exit(app.exec_())
