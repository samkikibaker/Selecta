MONGO_URI = "mongodb+srv://samkikibaker:gZoJKxxo4sBwxQiX@cluster0.khplbp6.mongodb.net/"
DB = "db"
JWT_SECRET = "12345"
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
API_URL = "http://localhost:8080"

import os
import sys
from pathlib import Path


def get_local_app_data_dir():
    if sys.platform == "darwin":  # macOS
        return Path.home() / "Library" / "Application Support" / "Selecta"
    elif sys.platform == "win32":  # Windows
        return Path(os.getenv('APPDATA')) / "Selecta"  # usually Roaming AppData
    else:
        # Linux / other - use XDG base dir spec
        return Path(os.getenv('XDG_CONFIG_HOME', Path.home() / ".config")) / "Selecta"

def get_log_dir():
    if sys.platform == "darwin":
        # macOS logs path
        return Path.home() / "Library" / "Logs" / "Selecta"
    elif sys.platform == "win32":
        # Windows logs path, using LOCALAPPDATA for logs
        local_app_data = os.getenv('LOCALAPPDATA')
        if local_app_data:
            return Path(local_app_data) / "Selecta" / "Logs"
        else:
            # fallback to APPDATA if LOCALAPPDATA not set
            app_data = os.getenv('APPDATA', Path.home() / "AppData" / "Roaming")
            return Path(app_data) / "Selecta" / "Logs"
    else:
        # Linux / Unix-like, use ~/.local/share/<app>/logs or ~/.cache/<app>/logs
        xdg_data_home = os.getenv('XDG_DATA_HOME', Path.home() / ".local" / "share")
        return Path(xdg_data_home) / "Selecta" / "logs"
    
    
def resource_path(relative_path: str) -> Path:
    """Get absolute path to resource, works for dev and for PyInstaller .app bundle"""
    if hasattr(sys, "_MEIPASS"):  # PyInstaller uses _MEIPASS
        return Path(sys._MEIPASS) / relative_path
    return Path(__file__).parent / relative_path


local_app_data_dir = get_local_app_data_dir()
log_dir = get_log_dir()