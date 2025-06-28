import librosa
import numpy as np

from pathlib import Path

from selecta.logger import generate_logger
from selecta.yamnet_model import yamnet_model

logger = generate_logger()

class Song:
    """Class to represent a song"""

    def __init__(self, path: Path):
        self.path = path
        self.name = path.name
        self.yamnet_embeddings = self.extract_audio_embeddings(self.path)
        self.simplified_yamnet_embeddings = self.collapse_matrix(self.yamnet_embeddings)
        del self.yamnet_embeddings  # Remove to reduce cache size

    @staticmethod
    def extract_audio_features(path: Path):
        """
        Extracts audio features from a given file path using librosa.

        Args:
            path (str): The file path of the audio file.

        Returns:
            tuple: A tuple containing:
                - audio (np.ndarray): The audio time series.
                - sampling_rate (int): The sampling rate of the audio file.
        """

        # Load the audio file with librosa
        audio, sampling_rate = librosa.load(path, sr=16000, mono=True, offset=0, duration=120)

        return audio, sampling_rate

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
            audio, sampling_rate = Song.extract_audio_features(path)

            # Normalize to the range [-1, 1]
            max_abs_value = float(np.max(np.abs(audio), axis=0))
            if max_abs_value == 0:
                max_abs_value = 1  # Avoid division by zero by setting max_abs_value to 1 where it is 0
            audio /= max_abs_value

            # # Run through YamNet model to extract embeddings
            # _, embeddings, _ = yamnet_model(audio)
            # yamnet_embeddings = np.array(embeddings)

            # Run through YamNet model to extract embeddings
            outputs_dict = yamnet_model(audio)
            class_scores = outputs_dict["output_0"].numpy()
            yamnet_embeddings = outputs_dict["output_1"].numpy()
            log_mel = outputs_dict["output_2"].numpy()

            return yamnet_embeddings

        except Exception as e:
            logger.error(f"Error loading or processing audio file {path}: {e}")
            raise e
            # return None

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
