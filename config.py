import multiprocessing

from tensorflow_hub import load

# yamnet_model_handle = 'https://www.kaggle.com/models/google/yamnet/TensorFlow2/yamnet/1'
yamnet_model_path = "yamnet-tensorflow2-yamnet-v1"
yamnet_model = load(yamnet_model_path)

# How many CPUs to run parallel processing on
num_processes = multiprocessing.cpu_count()  # Number of available CPU cores
