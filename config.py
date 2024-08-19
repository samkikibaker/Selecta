import multiprocessing

from tensorflow_hub import load

# Where to look for songs
root_directory = '/Users/sambaker/Downloads/Music/Bandcamp/1. Home Listening'
# root_directory = '/Users/sambaker/Downloads/Music/Bandcamp/2. Warm Up'
# root_directory = '/Users/sambaker/Downloads/Music/Bandcamp/3. Middle'
# root_directory = '/Users/sambaker/Downloads/Music/Bandcamp/4. Peak'
# root_directory = '/Users/sambaker/Downloads/Music/Bandcamp/5. End'
# root_directory = '/Users/sambaker/Downloads/Music/DJ/IFL_Throwback'

cache_path = f"cache/{root_directory.split('/')[-1]}"

# yamnet_model_handle = 'https://kaggle.com/models/google/yamnet/frameworks/TensorFlow2/variations/yamnet/versions/1'
yamnet_model_handle = 'https://www.kaggle.com/models/google/yamnet/TensorFlow2/yamnet/1'
yamnet_model = load(yamnet_model_handle)

# How many songs to send each round
num_roots = 5

# How many CPUs to run parallel processing on
num_processes = multiprocessing.cpu_count()  # Number of available CPU cores

# After how many seconds to stop the training early
max_training_time_seconds = 60

# How long to try optimise the combinations to send back to the user
combination_testing_time_seconds = 10

