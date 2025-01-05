import multiprocessing
import os
import fnmatch
import random
import joblib
import numpy as np

from sklearn.preprocessing import LabelBinarizer

from old.classes.song import Song
from config import num_roots, root_directory, num_processes, cache_path


class DataModel:
    """Class to represent groups of songs.joblib"""

    def __init__(self):
        self.all_song_paths, self.sorted_songs = self.get_sorted_song_paths(root_directory)
        self.song_objects = self.load_or_create_song_objects()

        self.categories = list(set(song.category for song in self.song_objects))
        self.category_encoder = LabelBinarizer().fit(self.categories)
        self.song_objects = self.encode_categories()

        self.song_objects = self.provide_initial_examples()

        self.num_uncategorised_songs = len([song for song in self.song_objects if not song.is_categorised])
        self.num_categorised_songs = len([song for song in self.song_objects if song.is_categorised])

    @staticmethod
    def get_sorted_song_paths(path):
        """Get the paths to all songs.joblib and which category they fall into"""
        mp3_file_paths = []
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in fnmatch.filter(filenames, "*.mp3"):
                mp3_path = os.path.abspath(os.path.join(dirpath, filename))
                mp3_file_paths.append(mp3_path)
        sorted_songs_dict = {}
        for file in mp3_file_paths:
            song_name = file.split(f"{path}/")[-1].split("/")[-1]
            song_category = file.split(f"{path}/")[-1].split(f"/{song_name}")[0]
            if not sorted_songs_dict.get(song_category):
                sorted_songs_dict[song_category] = []
            sorted_songs_dict[song_category].append(song_name)
        return mp3_file_paths, sorted_songs_dict

    def load_or_create_song_objects(self):
        if os.path.exists(cache_path):
            song_objects = joblib.load(cache_path)
        else:
            song_objects = self.create_and_cache_song_objects()
        return song_objects

    @staticmethod
    def create_song_object(path):
        song = Song(path)
        print(f"Created song object for song {song.name}")
        return song

    def create_and_cache_song_objects(self):
        pool = multiprocessing.Pool(processes=num_processes)
        song_objects = pool.map(self.create_song_object, self.all_song_paths)
        pool.close()
        pool.join()

        if os.path.exists(cache_path):
            os.remove(cache_path)
        joblib.dump(song_objects, cache_path)
        return song_objects

    def provide_initial_examples(self):
        """Select example songs.joblib in each category"""
        for category in self.categories:
            songs_in_category = [song for song in self.song_objects if song.category == category]
            if len(songs_in_category) <= num_roots:
                root_song_objects = songs_in_category
            else:
                root_song_objects = random.sample(songs_in_category, num_roots)
            for song in root_song_objects:
                song.is_root = True
                song.is_categorised = True
                song.predicted_category = song.category
        return self.song_objects

    def encode_categories(self):
        for song in self.song_objects:
            # Use the fitted encoder to transform the category
            num_rows = song.yamnet_embeddings.shape[0]
            category_column = np.full((num_rows, 1), song.category)
            category_encoded = self.category_encoder.transform(category_column)
            song.category_encoded = category_encoded

        return self.song_objects
