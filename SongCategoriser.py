import os
import fnmatch
import joblib
import librosa
import numpy as np
import pandas as pd
import multiprocessing

from scipy.spatial.distance import cdist
from tqdm import tqdm

from config import num_processes, yamnet_model

multiprocessing.set_start_method("spawn", force=True)


class Song:
    """Class to represent a song"""

    def __init__(self, path):
        self.path = path
        self.name = self.get_song_name_from_path()
        self.yamnet_embeddings = self.extract_audio_features()
        self.simplified_yamnet_embeddings = self.collapse_matrix(self.yamnet_embeddings)
        del self.yamnet_embeddings

    def get_song_name_from_path(self):
        song_name = self.path.split("/")[-1]
        return song_name

    def extract_audio_features(self):
        try:
            # Load the audio file with librosa
            try:
                audio, sampling_rate = librosa.load(self.path, sr=16000, mono=True, offset=30, duration=60)
            except librosa.util.exceptions.ParameterError:
                print(f"Offset exceeds file length for {self.path}, loading from beginning instead.")
                audio, sampling_rate = librosa.load(self.path, sr=16000, mono=True, offset=0, duration=60)

            # Normalise to the range [-1, 1]
            max_abs_value = float(np.max(np.abs(audio), axis=0))
            if max_abs_value == 0:
                max_abs_value = 1  # Avoid division by zero by setting max_abs_value to 1 where it is 0
            audio /= max_abs_value

            # Run through yamnet model to extract embeddings
            _, embeddings, _ = yamnet_model(audio)
            yamnet_embeddings = np.array(embeddings)

            return yamnet_embeddings

        except Exception as e:
            print(f"Error loading or processing audio file {self.path}: {e}")
            return None

    @staticmethod
    def collapse_matrix(arr, group_size=100):
        if arr is None:
            return None

        n, m = arr.shape
        # Calculate the number of full groups
        full_groups = n // group_size
        # Handle leftovers (if any)
        leftover_rows = n % group_size

        # Reshape the array into (full_groups, group_size, m), and average across the group axis
        if leftover_rows > 0:
            arr_full_groups = arr[: full_groups * group_size].reshape(full_groups, group_size, m)
            collapsed_matrix = np.mean(arr_full_groups, axis=1)

            # Average the remaining rows if there are any leftover
            leftover_matrix = np.mean(arr[full_groups * group_size :], axis=0, keepdims=True)
            collapsed_matrix = np.vstack([collapsed_matrix, leftover_matrix])
        else:
            arr_full_groups = arr.reshape(full_groups, group_size, m)
            collapsed_matrix = np.mean(arr_full_groups, axis=1)

        return collapsed_matrix


class SongCategoriser:
    def __init__(self):
        self.song_paths = self.get_song_paths("songs/")
        self.song_objects = self.load_or_create_song_objects()
        assert len(self.song_objects) > 0, f"No songs found in songs folder"
        self.similarity_matrix = self.compute_similarity_matrix()

    @staticmethod
    def get_song_paths(path):
        """Get the paths to all songs and which category they fall into"""
        mp3_file_paths = []
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in fnmatch.filter(filenames, "*.mp3"):
                mp3_path = os.path.abspath(os.path.join(dirpath, filename))
                mp3_file_paths.append(mp3_path)
        print(f"MP3 paths: {mp3_file_paths}")
        return mp3_file_paths

    def load_or_create_song_objects(self):
        try:
            song_objects = joblib.load("cache/songs")
        except FileNotFoundError:
            song_objects = self.create_and_cache_song_objects()
        return song_objects

    @staticmethod
    def create_song_object(path):
        song = Song(path)
        print(f"Created song object for song {song.name}")
        return song

    def create_and_cache_song_objects(self):
        # Use tqdm_map to show progress
        with multiprocessing.pool.ThreadPool(processes=num_processes) as pool:
            song_objects = list(
                tqdm(
                    pool.imap(self.create_song_object, self.song_paths),
                    total=len(self.song_paths),
                )
            )

        pool.close()
        pool.join()

        # Save to cache
        if os.path.exists("cache/songs"):
            os.remove("cache/songs")
        joblib.dump(song_objects, "cache/songs")

        return song_objects

    def compute_similarity_matrix(self):
        # Get song names
        song_names = [song.name for song in self.song_objects]

        # Collect all embeddings and their song indices
        embeddings = []
        song_indices = []
        for i, song in enumerate(self.song_objects):
            if song.simplified_yamnet_embeddings is not None:
                embeddings.append(song.simplified_yamnet_embeddings)
                song_indices.extend([i] * song.simplified_yamnet_embeddings.shape[0])

        embeddings = np.vstack(embeddings)  # Stack all embeddings
        song_indices = np.array(song_indices)  # Convert indices to numpy array

        # Compute all pairwise distances
        distances = cdist(embeddings, embeddings, metric="cosine")

        # Initialize similarity matrix
        similarity_matrix = pd.DataFrame(np.nan, index=song_names, columns=song_names)

        # Use numpy's upper triangle index for efficient iteration
        upper_triangle_indices = np.triu_indices(len(self.song_objects), k=1)

        # Iterate over unique song pairs using combinations and tqdm for progress tracking
        for i, j in tqdm(
            zip(upper_triangle_indices[0], upper_triangle_indices[1]),
            total=len(upper_triangle_indices[0]),
            desc="Computing similarity matrix",
        ):
            mask1 = song_indices == i
            mask2 = song_indices == j
            mean_distance = distances[mask1][:, mask2].mean()

            # Direct assignment with .iloc
            similarity_matrix.iloc[i, j] = mean_distance
            similarity_matrix.iloc[j, i] = mean_distance

        return similarity_matrix


if __name__ == "__main__":
    try:
        song_categoriser = joblib.load("cache/song_categoriser")
    except FileNotFoundError:
        song_categoriser = SongCategoriser()
        joblib.dump(song_categoriser, "cache/song_categoriser")
