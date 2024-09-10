import random
import librosa
import numpy as np

from config import root_directory, yamnet_model


class Song:
    """Class to represent a song"""

    def __init__(
            self,
            path,

    ):
        self.path = path
        self.is_categorised = False
        self.is_root = False
        self.name = self.get_song_name_from_path()
        self.category = self.get_song_category_from_path()
        self.category_encoded = None
        self.yamnet_embeddings, self.log_mel_spectrogram = self.extract_audio_features()
        self.aggregated_yamnet_embeddings = np.mean(self.yamnet_embeddings, axis=0)
        self.predicted_category = None
        self.predicted_category_encoded = None

    def get_song_category_from_path(self):
        song_category = self.path.split(f"{root_directory}/")[-1].split("/")[0]
        return song_category

    def get_song_name_from_path(self):
        song_name = self.path.split("/")[-1]
        return song_name

    def extract_audio_features(self):

        try:
            # Load the audio file with librosa
            audio, sampling_rate = librosa.load(self.path, sr=None)

            # Convert to mono if the audio is stereo
            if audio.ndim > 1:
                audio = librosa.to_mono(audio)

            # Resample to 16 kHz
            audio = librosa.resample(audio, orig_sr=sampling_rate, target_sr=16000)

            # Normalise to the range [-1, 1]
            max_abs_value = float(np.max(np.abs(audio), axis=0))
            if max_abs_value == 0:
                max_abs_value = 1  # Avoid division by zero by setting max_abs_value to 1 where it is 0
            audio /= max_abs_value

            scores, embeddings, log_mel_spectrogram = yamnet_model(audio)

            yamnet_embeddings = np.array(embeddings)
            log_mel_spectrogram = np.array(log_mel_spectrogram)

            return yamnet_embeddings, log_mel_spectrogram

        except Exception as e:
            print(f"Error loading or processing audio file {self.path}: {e}")
            return None
