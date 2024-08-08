from math import floor
import librosa
from config import root_directory, num_mfcc
import tensorflow as tf
import tensorflow_io as tfio


class Song:
    """Class to represent a song"""

    def __init__(
            self,
            path,
            is_categorised=False,

    ):
        self.path = path
        self.is_categorised = is_categorised
        self.name = self.get_song_name_from_path()
        self.category = self.get_song_category_from_path()
        self.mfcc_features = self.extract_mfcc_features()
        self.mono_wav_features = self.load_wav_16k_mono()
        self.predicted_category = None

    def get_song_category_from_path(self):
        song_category = self.path.split(f"{root_directory}/")[-1].split("/")[0]
        return song_category

    def get_song_name_from_path(self):
        song_name = self.path.split("/")[-1]
        return song_name

    def extract_mfcc_features(self):
        """Turn an audio file into an mfcc feature representation"""
        try:
            audio, sampling_rate = librosa.load(self.path)
            mfccs = librosa.feature.mfcc(y=audio, sr=sampling_rate, n_mfcc=num_mfcc, hop_length=floor(sampling_rate))
            features = mfccs.T
            return features
        except Exception as e:
            song_name = self.path.split("/")[-1]
            print(f"Error extracting features for {song_name}: {e}")
            return None

    @tf.function
    def load_wav_16k_mono(self):
        """ Load a WAV file, convert it to a float tensor, resample to 16 kHz single-channel audio. """
        file_contents = tf.io.read_file(self.path)
        wav, sample_rate = tf.audio.decode_wav(
            file_contents,
            desired_channels=1)
        wav = tf.squeeze(wav, axis=-1)
        sample_rate = tf.cast(sample_rate, dtype=tf.int64)
        wav = tfio.audio.resample(wav, rate_in=sample_rate, rate_out=16000)
        return wav
