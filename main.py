import os
from selecta.SongProcessorDesktop import SongProcessorDesktop
from pathlib import Path

documents_folder = os.path.expanduser("~/Documents/My Music/Bandcamp/1. Home Listening")

mp3_files = []
for root, dirs, files in os.walk(documents_folder):
    for file in files:
        if file.lower().endswith(".mp3"):
            full_path = os.path.join(root, file)
            mp3_files.append(Path(full_path))

if __name__ == "__main__":
    song_processor_desktop = SongProcessorDesktop(
        email="samkikibaker@hotmail.co.uk",
        local_song_paths=mp3_files
)
