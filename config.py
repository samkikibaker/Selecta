import multiprocessing

from tensorflow_hub import load

# Where to look for songs
# root_directory = '/Users/sambaker/Documents/Music/Bandcamp/1. Home Listening'
# root_directory = '/Users/sambaker/Documents/Music/Bandcamp/2. Warm Up'
# root_directory = '/Users/sambaker/Documents/Music/Bandcamp/3. Middle'
# root_directory = '/Users/sambaker/Documents/Music/Bandcamp/4. Peak'
# root_directory = '/Users/sambaker/Documents/Music/Bandcamp/5. End'
root_directory = '/Users/sambaker/Documents/Music/DJ/IFL_Throwback'

cache_path = f"cache/{root_directory.split('/')[-1]}"

# yamnet_model_handle = 'https://kaggle.com/models/google/yamnet/frameworks/TensorFlow2/variations/yamnet/versions/1'
yamnet_model_handle = 'https://www.kaggle.com/models/google/yamnet/TensorFlow2/yamnet/1'
yamnet_model = load(yamnet_model_handle)

# How many songs to send each round
num_roots = 1

# How many of the least confident predictions to send to the user each round
num_manual_per_round = 10

# How many CPUs to run parallel processing on
num_processes = 3  # Number of available CPU cores

# After how many seconds to stop the training early
max_training_time_seconds = 60

# What level of confidence a prediction must have to pass and be categorised
prediction_confidence_threshold = 0.6
