from math import floor
import keras
import numpy as np

from keras.models import Sequential
from keras.layers import Conv1D, MaxPooling1D, Flatten, Dense, Dropout, BatchNormalization, Activation, Input
from keras.callbacks import EarlyStopping
from keras.regularizers import l1, l2
from keras.optimizers import Adam
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC

from classes.early_stopping import TimeBasedStopping
from config import max_training_time_seconds, combination_testing_time_seconds


class Model:
    def __init__(self, data_model=None):
        self.data_model = data_model
        self.train_test_data = self.split_data_train_test()
        self.transfer_learning_model = self.configure_transfer_learning_model()
        self.transfer_learning_model = self.fit_transfer_learning_model()
        self.predict_song_categories()

    def split_data_train_test(self):
        """Split the data into training and test sets"""
        train_test_data = {}
        X_train, X_test, y_train, y_test = [], [], [], []
        for song in self.data_model.song_objects:
            # Use already categorised songs as training data
            if song.is_categorised:
                y_train.append(song.category_encoded)
                X_train.append(song.yamnet_embeddings)
            else:
                y_test.append(song.category_encoded)
                X_test.append(song.yamnet_embeddings)

        X_train = np.vstack(X_train)
        X_test = np.vstack(X_test)
        y_train = np.vstack(y_train)
        y_test = np.vstack(y_test)

        X_train = np.reshape(X_train, (X_train.shape[0], X_train.shape[1], 1))

        train_test_data = {
            "X_train": X_train,
            "X_test": X_test,
            "y_train": y_train,
            "y_test": y_test,
        }
        return train_test_data

    def configure_transfer_learning_model(self):
        dense_layer_size = self.train_test_data['y_train'].shape[1]  # Number of categories

        seq_model = Sequential([
            Flatten(),
            Dense(16, activation='relu', kernel_regularizer=l2(0.01)),
            Dense(dense_layer_size, activation='softmax', kernel_regularizer=l2(0.01))
        ])

        seq_model.summary()
        return seq_model

    def fit_transfer_learning_model(self):
        optimizer = Adam(learning_rate=0.1)  # Set your desired learning rate here

        self.transfer_learning_model.compile(optimizer=optimizer, loss='categorical_crossentropy', metrics=['accuracy'])

        # Stop early if accuracy doesn't improve for 5 consecutive epochs
        early_stopping = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)

        # Stop if max_training_time_seconds time elapses
        time_based_stopping = TimeBasedStopping(max_training_time_seconds)

        callbacks = [early_stopping, time_based_stopping]
        fitted_model = self.transfer_learning_model.fit(
            self.train_test_data['X_train'],
            self.train_test_data['y_train'],
            batch_size=256,
            epochs=100,
            callbacks=callbacks,
            validation_split=0.1)

        return fitted_model

    def predict_song_categories(self):
        for song in self.data_model.song_objects:
            predictions = self.transfer_learning_model.model.predict(song.yamnet_embeddings)

            # Average predictions across segments and choose the category with the highest overall prediction
            avg_prediction = np.mean(predictions, axis=0)
            predicted_category_encoded = np.argmax(avg_prediction)
            song.predicted_category = self.data_model.category_encoder.classes_[predicted_category_encoded]

            # TODO - Validate that this approach is worse than above
            # Categorise each segment then choose the modal category across all segments
            # max_columns = np.argmax(predictions, axis=1)
            # counts = np.bincount(max_columns, minlength=predictions.shape[1])
            # predicted_category_encoded = np.argmax(counts)
            # song.predicted_category = self.data_model.category_encoder.classes_[predicted_category_encoded]

        accuracy = len(
            [song for song in self.data_model.song_objects if song.predicted_category == song.category and not song.is_categorised]
        ) / len(
            [song for song in self.data_model.song_objects if not song.is_categorised]
        )
        print(f"Accuracy: {accuracy}")



