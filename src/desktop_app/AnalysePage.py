import pandas as pd
from PyQt5.QtCore import Qt, QThreadPool
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTableView,
    QHeaderView,
    QAbstractItemView,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QProgressBar,
)
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from pathlib import Path

from desktop_app.AnalysisWorker import AnalysisWorker
from selecta.logger import generate_logger

# Logger
logger = generate_logger()


class AnalysePage(QMainWindow):
    def __init__(self, email: str = None, songs_df: pd.DataFrame = None, access_token: str = None):
        super().__init__()
        self.setWindowTitle("Selecta")
        self.email = email
        self.access_token = access_token
        self.songs_df = songs_df
        self.added_songs_df = pd.DataFrame()
        self.new_songs_df = pd.DataFrame()

        # Central widget and layout
        central_widget = QWidget()
        main_layout = QHBoxLayout()  # left menu + right content
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # === Left panel (sidebar menu) ===
        left_panel = QVBoxLayout()

        # Title
        title = QLabel("Analyse")
        title.setAlignment(Qt.AlignLeft)
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 16px;")
        left_panel.addWidget(title)

        # Add Songs button
        add_songs_button = QPushButton("Add Songs")
        add_songs_button.clicked.connect(self.select_folder)
        left_panel.addWidget(add_songs_button)

        # Analyse Songs button
        analyse_songs_button = QPushButton("Analyse Songs")
        analyse_songs_button.clicked.connect(self.analyse_songs)
        left_panel.addWidget(analyse_songs_button)

        # Status Label
        self.status_label = QLabel("Idle")
        left_panel.addWidget(self.status_label)

        # Progress Bars
        self.analysis_progress_bar = QProgressBar()
        self.analysis_progress_bar.setRange(0, 100)
        self.analysis_progress_bar.setValue(0)
        left_panel.addWidget(self.analysis_progress_bar)

        self.similarity_progress_bar = QProgressBar()
        self.similarity_progress_bar.setRange(0, 100)
        self.similarity_progress_bar.setValue(0)
        left_panel.addWidget(self.similarity_progress_bar)

        left_panel.addStretch()

        # === Right panel (song table) ===
        self.table_view = QTableView()
        self.table_model = self.create_table_model(self.new_songs_df)
        self.table_view.setModel(self.table_model)

        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_view.setSortingEnabled(True)

        # === Assemble layout ===
        main_layout.addLayout(left_panel, stretch=1)
        main_layout.addWidget(self.table_view, stretch=3)

        self.threadpool = QThreadPool()

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
                added_songs.append({"name": file_path.name, "location": file_path})
            self.added_songs_df = pd.DataFrame(added_songs)
            self.new_songs_df = pd.concat([self.added_songs_df, self.songs_df, self.songs_df]).drop_duplicates(
                keep=False
            )

            self.table_model = self.create_table_model(self.new_songs_df)
            self.table_view.setModel(self.table_model)

            QMessageBox.information(None, "Added Songs", f"Added {len(self.new_songs_df)} songs not already analysed")

    def analyse_songs(self):
        if self.new_songs_df.empty:
            QMessageBox.warning(None, "No Songs", "Please add new songs before analysing.")
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
