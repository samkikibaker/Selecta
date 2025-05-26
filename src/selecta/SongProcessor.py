import os
import joblib
import numpy as np
import pandas as pd
import multiprocessing

from scipy.spatial.distance import cdist
from tqdm import tqdm

from selecta.logger import generate_logger
from blob_storage import create_blob_container_client, download_blobs, upload_blob
from Song import Song

multiprocessing.set_start_method("spawn", force=True)

logger = generate_logger()
# Download similarity matrix and songs cache from blob storage (if they exist)
# List all uploaded songs from blob storage
# Check the similarity matrix and songs cache to see which songs need to be downloaded
# Download those songs and compute the yamnet embeddings (do this one by one, deleting the downloaded song to avoid
#   the container running out of memory)
# Add each song object to the songs object and upload it back to cloud storage at the end (then delete from the
#   container to optimise memory)
# Recompute the similarity matrix (might be easier to recompute the whole thing than just the parts that need to be
#   recomputed)
# Upload similarity matrix to blob storage


class SongProcessor:
    def __init__(self, email: str):
        self.email = email
        self.container_client = create_blob_container_client(storage_account="saselecta", container="containerselecta")
        self.similarity_matrix = self.get_similarity_matrix()
        self.songs_cache = self.get_songs_cache()
        self.songs_to_process = self.compute_songs_to_process()
        self.songs_cache = self.update_songs_cache()
        self.upload_songs_cache()
        self.similarity_matrix = self.compute_similarity_matrix()
        self.upload_similarity_matrix()

    def get_similarity_matrix(self):
        download_blobs(
            container_client=self.container_client,
            prefix=f"users/{self.email}/cache/similarity_matrix.joblib",
            local_dir_path=f"cache/",
        )
        similarity_matrix = joblib.load(f"cache/similarity_matrix.joblib")
        if similarity_matrix is None:
            similarity_matrix = []
        return similarity_matrix

    def get_songs_cache(self):
        download_blobs(
            container_client=self.container_client,
            prefix=f"users/{self.email}/cache/songs.joblib",
            local_dir_path=f"cache/",
        )
        songs = joblib.load(f"cache/songs.joblib")
        if songs is None:
            songs = []
        return songs

    def compute_songs_to_process(self):
        uploaded_songs = self.container_client.list_blob_names(name_starts_with=f"users/{self.email}/songs/")
        computed_songs = self.similarity_matrix.columns
        songs_to_process = list(set(uploaded_songs) - set(computed_songs))
        return songs_to_process

    def update_songs_cache(self):
        new_songs = []
        for song_blob_path in self.songs_to_process:
            download_blobs(
                container_client=self.container_client,
                prefix=song_blob_path,
                local_dir_path=f"songs/",
            )
            song_name = song_blob_path.split("/")[-1]
            song = Song(path=f"songs/{song_name}")
            new_songs.append(song)
            os.remove(f"songs/{song_name}")

        updated_songs_cache = self.songs_cache + new_songs
        return updated_songs_cache

    def upload_songs_cache(self):
        local_path = "cache/songs.joblib"
        joblib.dump(self.songs_cache, local_path)
        upload_blob(
            container_client=self.container_client,
            local_file_path=local_path,
            blob_path=f"users/{self.email}/cache/songs.joblib",
        )
        os.remove(local_path)

    def compute_similarity_matrix(self):
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

        return similarity_matrix

    def upload_similarity_matrix(self):
        local_path = "cache/similarity_matrix.joblib"
        joblib.dump(self.similarity_matrix, local_path)
        upload_blob(
            container_client=self.container_client,
            local_file_path=local_path,
            blob_path=f"users/{self.email}/cache/similarity_matrix.joblib",
        )
        os.remove(local_path)
