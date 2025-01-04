import time

from keras.callbacks import Callback

from config import max_training_time_seconds


class TimeBasedStopping(Callback):
    def __init__(self, max_time_seconds):
        self.max_time_seconds = max_time_seconds

    def on_train_begin(self, logs=None):
        self.start_time = time.time()

    def on_epoch_end(self, epoch, logs=None):
        current_time = time.time()
        if current_time - self.start_time > self.max_time_seconds:
            print(
                f"\n Ending training early as the  maximum training time ({max_training_time_seconds} seconds)"
                f" was reached")
            self.model.stop_training = True
