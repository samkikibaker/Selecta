import pandas as pd
from PyQt5.QtCore import QRunnable, pyqtSlot

from desktop_app.AnalysisWorkerSignals import AnalysisWorkerSignals
from selecta.SongProcessorDesktop import SongProcessorDesktop


class AnalysisWorker(QRunnable):
    def __init__(self, new_songs_df: pd.DataFrame = None, email: str = None):
        super().__init__()
        self.new_songs_df = new_songs_df
        self.email = email
        self.signals = AnalysisWorkerSignals()

    @pyqtSlot()
    def run(self):
        new_song_paths = list(self.new_songs_df["location"])
        song_processor = SongProcessorDesktop(
            email=self.email,
            local_song_paths=new_song_paths,
        )
        song_processor.run(signals=self.signals)
