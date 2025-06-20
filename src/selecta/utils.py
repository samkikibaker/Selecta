MONGO_URI = "mongodb+srv://samkikibaker:gZoJKxxo4sBwxQiX@cluster0.khplbp6.mongodb.net/"
DB = "db"
JWT_SECRET = "12345"
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
API_URL = "http://localhost:8080"

import sys
from pathlib import Path


def resource_path(relative_path: str) -> Path:
    """Get absolute path to resource, works for dev and for PyInstaller .app bundle"""
    if hasattr(sys, "_MEIPASS"):  # PyInstaller uses _MEIPASS
        return Path(sys._MEIPASS) / relative_path
    return Path(__file__).parent / relative_path
