from PyQt5.QtCore import QObject, pyqtSignal


class AnalysisWorkerSignals(QObject):
    """
    Defines the signals available from a running worker thread.
    status
        str idictating current status
    progress
        int indicating % progress

    """

    status = pyqtSignal(str)
    analysis_progress = pyqtSignal(int)
    similarity_progress = pyqtSignal(int)
