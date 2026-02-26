import pandas as pd
from PyQt5.QtCore import QRunnable, pyqtSlot

from app.AnalysisWorkerSignals import AnalysisWorkerSignals
from selecta.SongProcessorDesktop import SongProcessorDesktop


class AnalysisWorker(QRunnable):
    def __init__(self, new_songs_df: pd.DataFrame = None):
        super().__init__()
        self.new_songs_df = new_songs_df
        self.signals = AnalysisWorkerSignals()

    @pyqtSlot()
    def run(self):
        new_song_paths = list(self.new_songs_df["location"])
        song_processor = SongProcessorDesktop(
            local_song_paths=new_song_paths,
        )
        song_processor.run(signals=self.signals)
