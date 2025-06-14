import os
import pandas as pd
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QLabel
from dotenv import load_dotenv

from selecta.logger import generate_logger

# Logger
logger = generate_logger()

# Env vars
load_dotenv()
API_URL = os.getenv("API_URL")


class PlaylistsPage(QMainWindow):
    def __init__(self, email: str = None, songs_df: pd.DataFrame = None, access_token: str = None):
        super().__init__()
