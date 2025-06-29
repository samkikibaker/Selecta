import httpx
import librosa
import numpy as np

from pathlib import Path

from selecta.logger import generate_logger
from selecta.utils import API_URL

logger = generate_logger()


class Song:
    """Class to represent a song"""

    def __init__(self, path: Path):
        self.path = path
        self.name = path.name
        self.yamnet_embeddings = None
        self.simplified_yamnet_embeddings = None

    def extract_audio_embeddings(self, path: Path):
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
            audio, sampling_rate = librosa.load(path, sr=16000, mono=True, offset=0, duration=120)

            # Normalize to the range [-1, 1]
            max_abs_value = float(np.max(np.abs(audio), axis=0))
            if max_abs_value == 0:
                max_abs_value = 1  # Avoid division by zero by setting max_abs_value to 1 where it is 0
            audio /= max_abs_value

            # Convert to list of floats for JSON
            audio_list = audio.tolist()

            # Post to get_embeddings endpoint
            with httpx.Client() as client:
                response = client.post(f"{API_URL}/get_embeddings", json={"audio": audio_list})
                if response.status_code == 200:
                    yamnet_embeddings = response.json().get("yamnet_embeddings")
                    return np.array(yamnet_embeddings)
                else:
                    logger.error(f"Error calling get_embeddings endpoint: {response.text}")
                    return None

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
