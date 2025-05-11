import os
import fnmatch
import joblib
import librosa
import numpy as np
import pandas as pd
import multiprocessing
import hashlib

from scipy.spatial.distance import cdist
from tqdm import tqdm
from pathlib import Path

from config import num_processes, yamnet_model
from selecta.logger import logger

multiprocessing.set_start_method("spawn", force=True)


class Song:
    """Class to represent a song"""

    def __init__(self, path):
        self.path = path
        self.name = self.get_song_name_from_path(self.path)
        self.yamnet_embeddings = self.extract_audio_embeddings(self.path)
        self.simplified_yamnet_embeddings = self.collapse_matrix(self.yamnet_embeddings)
        del self.yamnet_embeddings  # Remove to reduce cache size

    @staticmethod
    def get_song_name_from_path(path: str):
        """
        Extracts the song name from a given file path.

        Args:
            path (str): The file path of the song.

        Returns:
            str: The song name, extracted as the last component of the path.
        """
        song_name = path.split("/")[-1]
        return song_name

    @staticmethod
    def extract_audio_features(path: str):
        """
        Extracts audio features from a given file path using librosa.

        This method loads an audio file and returns the audio data and its sampling rate.
        If the specified offset exceeds the file's length, it loads the audio from the beginning instead.

        Args:
            path (str): The file path of the audio file.

        Returns:
            tuple: A tuple containing:
                - audio (np.ndarray): The audio time series.
                - sampling_rate (int): The sampling rate of the audio file.
        """

        # Load the audio file with librosa
        audio, sampling_rate = librosa.load(path, sr=16000, mono=True, offset=30, duration=120)

        if len(audio) == 0:
            logger.info(f"Offset exceeds file length for {path}, loading from beginning instead.")
            audio, sampling_rate = librosa.load(path, sr=16000, mono=True, offset=0, duration=120)

        return audio, sampling_rate

    @staticmethod
    def extract_audio_embeddings(path: str):
        """
        Extracts audio embeddings from a given file path using the YamNet model.

        This method processes an audio file by normalizing its amplitude to the range [-1, 1]
        and then extracting embeddings using a pre-trained YamNet model.

        Args:
            path (str): The file path of the audio file.

        Returns:
            np.ndarray or None: A NumPy array containing the extracted embeddings, or None
                                if an error occurs during loading or processing.
        """
        try:
            # Extract audio
            audio, sampling_rate = Song.extract_audio_features(path)

            # Normalize to the range [-1, 1]
            max_abs_value = float(np.max(np.abs(audio), axis=0))
            if max_abs_value == 0:
                max_abs_value = 1  # Avoid division by zero by setting max_abs_value to 1 where it is 0
            audio /= max_abs_value

            # Run through YamNet model to extract embeddings
            _, embeddings, _ = yamnet_model(audio)
            yamnet_embeddings = np.array(embeddings)

            return yamnet_embeddings

        except Exception as e:
            logger.error(f"Error loading or processing audio file {path}: {e}")
            return None

    @staticmethod
    def collapse_matrix(arr: np.array, group_size: int = 100):
        """
        Reduces the number of rows in a matrix by grouping and averaging.

        This method collapses a 2D array by dividing its rows into groups of a specified size
        (`group_size`) and averaging the values within each group. If the number of rows
        is not evenly divisible by `group_size`, any leftover rows are averaged separately
        and appended to the result.

        Args:
            arr (np.array): The input 2D array to be collapsed.
            group_size (int): The number of rows in each group for averaging. Default is 100.

        Returns:
            np.array or None: A 2D array with reduced rows where each row is the average
                              of a group, or None if the input array is None.
        """
        if arr is None:
            return None

        num_rows, num_cols = arr.shape
        # Calculate the number of full groups
        full_groups = num_rows // group_size
        # Handle leftovers (if any)
        leftover_rows = num_rows % group_size

        # Reshape the array into (full_groups, group_size, num_cols), and average across the group axis
        if leftover_rows > 0:
            arr_full_groups = arr[: full_groups * group_size].reshape(full_groups, group_size, num_cols)
            collapsed_matrix = np.mean(arr_full_groups, axis=1)

            # Average the remaining rows if there are any leftover
            leftover_matrix = np.mean(arr[full_groups * group_size :], axis=0, keepdims=True)
            collapsed_matrix = np.vstack([collapsed_matrix, leftover_matrix])
        else:
            arr_full_groups = arr.reshape(full_groups, group_size, num_cols)
            collapsed_matrix = np.mean(arr_full_groups, axis=1)

        return collapsed_matrix


class SongCategoriser:
    """Class to process the songs and compute similarities"""

    def __init__(self, dir_path: str):
        # Define cache file names
        self.dir_path = dir_path
        self.dir_path_hash = hashlib.md5(str(self.dir_path).encode()).hexdigest()
        self.songs_cache_filename = f"songs-{self.dir_path_hash}"
        self.similarity_matrix_cache_filename = f"similarity_matrix-{self.dir_path_hash}"

        # Get song paths
        self.song_paths = self.get_song_paths(path=self.dir_path)

        # Load or create song objects
        self.song_objects = self.load_or_create_song_objects()
        self.song_objects = self.remove_songs_with_errors()

        # Compute similarity matrix
        self.similarity_matrix = self.load_or_compute_similarity_matrix()

    @staticmethod
    def get_song_paths(path: str = "songs/"):
        """
        Retrieves the file paths of all MP3 songs within a directory.

        This method walks through the given directory and its subdirectories,
        identifies all `.mp3` files, and returns their absolute paths.

        Args:
            path (str): The root directory to search for MP3 files.
                        Defaults to "songs/".

        Returns:
            list: A list of absolute file paths to all `.mp3` files found in the directory.
        """

        mp3_file_paths = []
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in fnmatch.filter(filenames, "*.mp3"):
                mp3_path = os.path.abspath(os.path.join(dirpath, filename))
                mp3_file_paths.append(mp3_path)

        return mp3_file_paths

    def load_or_create_song_objects(self):
        """
        Loads cached song objects if available, or creates and caches them if not.

        This method attempts to load a list of pre-processed song objects from a cached file.
        If the file does not exist, it generates the song objects using the
        `create_and_cache_song_objects` method, caches them for future use, and returns the result.

        Returns:
            list: A list of song objects, either loaded from the cache or freshly created.
        """
        try:
            song_objects = joblib.load(Path(f"cache/{self.songs_cache_filename}"))
        except FileNotFoundError:
            logger.info("No songs cache found, creating song objects...")
            song_objects = self.create_and_cache_song_objects()
        return song_objects

    @staticmethod
    def create_song_object(path: str):
        """
        Creates a Song object from a given file path.

        This method instantiates a `Song` object for the provided file path. It is designed
        to be used as a helper function in the `create_and_cache_song_objects` method, which
        processes multiple song paths in parallel to generate song objects.

        Args:
            path (str): The file path of the song.

        Returns:
            Song: A `Song` object created from the specified file path.
        """
        song = Song(path)
        return song

    def create_and_cache_song_objects(self):
        """
        Creates and caches Song objects from the available song paths.

        This method processes a list of song file paths, creating a `Song` object
        for each path in parallel using a thread pool to optimize performance.
        The resulting list of song objects is then saved to a cache file for future use.

        The method uses a progress bar (via `tqdm`) to visually display the status of the
        object creation process.

        Steps:
            1. Processes all song paths in parallel to create `Song` objects.
            2. Removes any existing cache file to avoid duplication.
            3. Saves the generated objects to a cache file.

        Returns:
            list: A list of `Song` objects created from the song paths.
        """
        # Use tqdm to show progress
        with multiprocessing.pool.ThreadPool(processes=num_processes) as pool:
            song_objects = list(
                tqdm(
                    pool.imap(self.create_song_object, self.song_paths),
                    total=len(self.song_paths),
                    desc="Processing Songs",
                )
            )

        pool.close()
        pool.join()

        # Save to cache
        joblib.dump(song_objects, Path(f"cache/{self.songs_cache_filename}"))
        logger.info("Cached song objects")

        return song_objects

    def remove_songs_with_errors(self):
        """
        This method filters out songs that encountered errors during their processing (i.e., those that have non-None
        'simplified_yamnet_embeddings'). It creates two lists: one for songs with errors and one for songs without errors.
        It logs the names of the songs with errors and their count. The function then returns the list of songs that
        were successfully processed (i.e., those without errors).

        Returns:
            list: A list of songs that did not encounter errors during processing.
        """
        # List songs with non-None simplified_yamnet_embeddings (those that had errors)
        songs_with_errors = [song for song in self.song_objects if song.simplified_yamnet_embeddings is None]

        # List songs without errors
        songs_without_errors = [song for song in self.song_objects if song.simplified_yamnet_embeddings is not None]

        # Log warnings about the songs with errors
        logger.warning(
            f"The following {len(songs_with_errors)} songs had errors in their processing so have been excluded:"
        )

        # Print each song name on a new line
        for song in songs_with_errors:
            logger.warning(f"- {song.name}")

        return songs_without_errors

    def load_or_compute_similarity_matrix(self):
        """
        Computes a pairwise similarity matrix for all songs using their embeddings.

        This method calculates the similarity between all songs in the collection based on
        their simplified YAMNet embeddings. It computes pairwise cosine distances and
        stores the results in a symmetric similarity matrix where each cell represents the
        average similarity between the embeddings of two songs.

        Steps:
            1. Collects song names and embeddings for all songs with valid embeddings.
            2. Computes pairwise cosine distances between all embeddings.
            3. Iterates over all unique song pairs to calculate the average similarity
               between their embeddings.
            4. Stores the similarity scores in a symmetric DataFrame with song names as
               row and column indices.

        Key Features:
            - Uses efficient upper triangular indexing to minimize redundant calculations,
              leveraging the property that similarity(i, j) = similarity(j, i).
            - Displays progress with a `tqdm` progress bar for transparency during computation.

        Returns:
            pd.DataFrame: A symmetric similarity matrix with song names as both row and column labels,
                          and average similarity scores as values. Cells contain NaN if a pair does
                          not have valid embeddings for comparison.
        """

        # Load if cache exists
        if os.path.exists(Path(f"cache/{self.similarity_matrix_cache_filename}")):
            similarity_matrix = joblib.load(Path(f"cache/{self.similarity_matrix_cache_filename}"))

        else:
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

            # Compute all pairwise distances between embeddings
            logger.info("Computing pairwise distances between song embeddings...")
            distances = cdist(embeddings, embeddings, metric="cosine")

            # Initialize an empty similarity matrix
            similarity_matrix = pd.DataFrame(np.nan, index=pd.Series(song_names), columns=pd.Series(song_names))

            # Use upper triangle index for efficient iteration
            upper_triangle_indices = np.triu_indices(len(self.song_objects), k=1)

            # Iterate over unique song pairs using combinations and tqdm for progress tracking
            for i, j in tqdm(
                zip(upper_triangle_indices[0], upper_triangle_indices[1]),
                total=len(upper_triangle_indices[0]),
                desc="Assessing Similarity",
            ):
                # Compute average distance
                mask1 = song_indices == i
                mask2 = song_indices == j
                mean_distance = distances[mask1][:, mask2].mean()

                # Assign in similarity matrix
                similarity_matrix.iloc[i, j] = mean_distance
                similarity_matrix.iloc[j, i] = mean_distance

            joblib.dump(similarity_matrix, Path(f"cache/{self.similarity_matrix_cache_filename}"))
            logger.info("Cached similarity matrix")

        return similarity_matrix
