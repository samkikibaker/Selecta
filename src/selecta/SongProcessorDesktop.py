import os
import sys

import joblib
import pickle
import numpy as np
import pandas as pd
import multiprocessing

from scipy.spatial.distance import cdist
from tqdm import tqdm
from pathlib import Path

from selecta.logger import generate_logger
from selecta.blob_storage import create_blob_container_client, download_blobs, upload_blob
from selecta.Song import Song, init_yamnet

logger = generate_logger()


def init_worker():
    init_yamnet()


def process_song(song_path):
    return Song(path=song_path)


class SongProcessorDesktop:
    def __init__(self, email: str, local_song_paths: list[Path]):
        self.email = email
        self.local_song_paths = local_song_paths
        self.container_client = create_blob_container_client(storage_account="saselecta", container="containerselecta")
        self.similarity_matrix = self.get_similarity_matrix()
        self.songs_cache = self.get_songs_cache()
        self.song_paths_to_process = self.compute_song_paths_to_process()
        self.analysis_progress_bar_max = len(self.song_paths_to_process)
        self.similarity_progress_bar_max = self.compute_similarity_progress_bar_max_value()
        self.analysis_progress_value = 0
        self.similarity_progress_value = 0

    def get_similarity_matrix(self):
        local_path = os.path.expanduser("~/cache/similarity_matrix.pickle")
        if os.path.exists(local_path):
            os.remove(local_path)
        download_blobs(
            container_client=self.container_client,
            prefix=f"users/{self.email}/cache/similarity_matrix.pickle",
            local_dir_path=os.path.expanduser("~/cache"),
        )
        try:
            with open(local_path, "rb") as f:
                similarity_matrix = pickle.load(f)
        except FileNotFoundError:
            similarity_matrix = pd.DataFrame()
        return similarity_matrix

    def get_songs_cache(self):
        local_path = os.path.expanduser("~/cache/songs.pickle")
        if os.path.exists(local_path):
            os.remove(local_path)
        download_blobs(
            container_client=self.container_client,
            prefix=f"users/{self.email}/cache/songs.pickle",
            local_dir_path=os.path.expanduser("~/cache"),
        )
        try:
            with open(local_path, "rb") as f:
                songs = pickle.load(f)
            os.remove(local_path)
        except FileNotFoundError:
            songs = []
        return songs

    def compute_song_paths_to_process(self):
        song_paths_to_process = []
        for local_path in self.local_song_paths:
            song_name = Path(local_path).name
            if song_name not in self.similarity_matrix.columns:
                song_paths_to_process.append(local_path)
        return song_paths_to_process

    def compute_similarity_progress_bar_max_value(self):
        future_songs_cache_len = len(self.songs_cache) + len(self.song_paths_to_process)
        upper_triangle_indices = np.triu_indices(future_songs_cache_len, k=1)
        num_similarities_to_compute = len(upper_triangle_indices[0])
        return num_similarities_to_compute

    def update_songs_cache(self, signals):
        new_songs = []
        with multiprocessing.Pool(initializer=init_worker, processes=multiprocessing.cpu_count()) as pool:
            for song in tqdm(
                pool.imap_unordered(process_song, self.song_paths_to_process),
                total=len(self.song_paths_to_process),
            ):
                new_songs.append(song)
                self.analysis_progress_value += 1
                analysis_progress_percentage = round(
                    100 * self.analysis_progress_value / self.analysis_progress_bar_max
                )
                signals.analysis_progress.emit(analysis_progress_percentage)

        updated_songs_cache = self.songs_cache + new_songs
        return updated_songs_cache

    def upload_songs_cache(self):
        local_path = os.path.expanduser("~/cache/songs.pickle")
        with open(local_path, "wb") as f:
            pickle.dump(self.songs_cache, f)
        upload_blob(
            container_client=self.container_client,
            local_file_path=local_path,
            blob_path=f"users/{self.email}/cache/songs.pickle",
        )
        os.remove(local_path)

    def compute_similarity_matrix_old(self, signals):
        # Get song names
        song_names = [song.name for song in self.songs_cache]

        # Collect all embeddings and their song indices
        embeddings = []
        song_indices = []
        for i, song in enumerate(self.songs_cache):
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
        upper_triangle_indices = np.triu_indices(len(self.songs_cache), k=1)

        # Iterate over unique song pairs using combinations and tqdm for progress tracking
        # for idx in tqdm(range(len(upper_triangle_indices[0])), desc="Assessing Similarity"):
        for idx in tqdm(range(len(upper_triangle_indices[0]))):
            i = upper_triangle_indices[0][idx]
            j = upper_triangle_indices[1][idx]
            # Compute average distance
            mask1 = song_indices == i
            mask2 = song_indices == j
            median_distance = np.median(distances[mask1][:, mask2])

            # Assign in similarity matrix
            similarity_matrix.iloc[i, j] = median_distance
            similarity_matrix.iloc[j, i] = median_distance

            self.similarity_progress_value += 1
            similarity_progress_percentage = round(
                100 * self.similarity_progress_value / self.similarity_progress_bar_max
            )
            signals.similarity_progress.emit(similarity_progress_percentage)

        return similarity_matrix

    def compute_similarity_matrix(self, signals):
        song_names = [song.name for song in self.songs_cache]

        # Gather embeddings and corresponding song indices
        embeddings = []
        song_indices = []
        for i, song in enumerate(self.songs_cache):
            if song.simplified_yamnet_embeddings is not None:
                embeddings.append(song.simplified_yamnet_embeddings)
                song_indices.extend([i] * song.simplified_yamnet_embeddings.shape[0])

        embeddings = np.vstack(embeddings)
        song_indices = np.array(song_indices)

        logger.info("Computing pairwise distances between song embeddings...")
        distances = cdist(embeddings, embeddings, metric="cosine")

        n_songs = len(self.songs_cache)
        similarity_matrix_data = np.full((n_songs, n_songs), np.nan)

        # Precompute masks for each song index once
        index_masks = [song_indices == i for i in range(n_songs)]

        upper_triangle_indices = np.triu_indices(n_songs, k=1)
        num_pairs = len(upper_triangle_indices[0])

        self.similarity_progress_bar_max = num_pairs
        similarity_progress_value = 0  # local for performance

        for idx in tqdm(range(num_pairs)):
            i = upper_triangle_indices[0][idx]
            j = upper_triangle_indices[1][idx]

            mask1 = index_masks[i]
            mask2 = index_masks[j]

            # This indexing avoids nested slicing
            distance_block = distances[np.ix_(mask1, mask2)]
            median_distance = np.median(distance_block)

            similarity_matrix_data[i, j] = median_distance
            similarity_matrix_data[j, i] = median_distance

            similarity_progress_value += 1
            if signals:
                signals.similarity_progress.emit(
                    round(100 * similarity_progress_value / self.similarity_progress_bar_max)
                )

        # Convert to DataFrame at the end
        similarity_matrix = pd.DataFrame(similarity_matrix_data, index=song_names, columns=song_names)
        return similarity_matrix

    def upload_similarity_matrix(self):
        local_path = os.path.expanduser("~/cache/similarity_matrix.pickle")
        with open(local_path, "wb") as f:
            pickle.dump(self.similarity_matrix, f)
        upload_blob(
            container_client=self.container_client,
            local_file_path=local_path,
            blob_path=f"users/{self.email}/cache/similarity_matrix.pickle",
        )
        os.remove(local_path)

    def run(self, signals=None):
        if getattr(sys, "frozen", False):
            multiprocessing.freeze_support()

        if signals:
            signals.status.emit("Analysing Songs...")
        self.songs_cache = self.update_songs_cache(signals=signals)
        self.upload_songs_cache()
        if signals:
            signals.status.emit("Computing Similarities...")
        self.similarity_matrix = self.compute_similarity_matrix(signals=signals)
        self.upload_similarity_matrix()
        if signals:
            signals.status.emit("Done")
