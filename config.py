import multiprocessing

# Where to look for songs
root_directory = '/Users/sambaker/Downloads/Music/Bandcamp/2. Warm Up'

# Where to cache processed songs
cache_path = 'cache/songs.joblib'


# How many mfcc coefficients to use (typically 10-20)
num_mfcc = 20

# How many songs to send each round
num_roots = 5

# How many CPUs to run parallel processing on
num_processes = multiprocessing.cpu_count()  # Number of available CPU cores

