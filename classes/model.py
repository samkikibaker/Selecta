import operator
from math import floor
import keras
import numpy as np
import math
import pandas as pd

from keras.models import Sequential
from keras.layers import Conv1D, MaxPooling1D, Flatten, Dense, Dropout, BatchNormalization, Activation, Input
from keras.callbacks import EarlyStopping
from keras.regularizers import l1, l2
from keras.optimizers import Adam
from sklearn.cluster import KMeans
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC

from classes.early_stopping import TimeBasedStopping
from config import max_training_time_seconds, prediction_confidence_threshold, num_manual_per_round


class AbstractModel:
    def __init__(self, data_model=None):
        self.data_model = data_model


class TransferLearningModel(AbstractModel):
    def __init__(self, data_model=None):
        super().__init__(data_model)
        self.train_test_data = self.split_data_train_test()
        self.model = self.configure_model()
        self.model = self.fit_model()
        self.predict_song_categories()
        self.investigate_confidence_threshold()
        self.assign_song_categories()
        self.manually_categorise_unconfident_songs()

    def split_data_train_test(self):
        """Split the data into training and test sets"""
        X_train, X_test, y_train, y_test = [], [], [], []
        for song in self.data_model.song_objects:
            if song.is_root:
                # If the song is a root use its true category and add it to the training data
                y_train.append(song.category_encoded)
                X_train.append(song.yamnet_embeddings)
            elif song.is_categorised:
                # If the song is not a root but has been categorised (i.e. predicted) use its predicted category and add it to the training
                # data
                y_train.append(song.predicted_category_encoded)
                X_train.append(song.yamnet_embeddings)
            else:
                # If the song has not been categorised add it to the test data
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

    def configure_model(self):
        dense_layer_size = self.train_test_data['y_train'].shape[1]  # Number of categories

        seq_model = Sequential([
            Flatten(),
            Dense(16, activation='relu', kernel_regularizer=l2(0.01)),
            Dense(dense_layer_size, activation='softmax', kernel_regularizer=l2(0.01))
        ])

        seq_model.summary()
        return seq_model

    def fit_model(self):
        optimizer = Adam(learning_rate=0.1)  # Set your desired learning rate here

        self.model.compile(optimizer=optimizer, loss='categorical_crossentropy', metrics=['accuracy'])

        # Stop early if accuracy doesn't improve for 5 consecutive epochs
        early_stopping = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)

        # Stop if max_training_time_seconds time elapses
        time_based_stopping = TimeBasedStopping(max_training_time_seconds)

        callbacks = [early_stopping, time_based_stopping]
        fitted_model = self.model.fit(
            self.train_test_data['X_train'],
            self.train_test_data['y_train'],
            batch_size=256,
            epochs=100,
            callbacks=callbacks,
            validation_split=0.1)

        return fitted_model

    def predict_song_categories(self):
        for song in self.data_model.song_objects:
            if not song.is_categorised:
                predictions = self.model.model.predict(song.yamnet_embeddings)

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

                # Compute the prediction confidence metric
                song.prediction_confidence_score = self.assess_prediction_confidence(avg_prediction)

        self.median_prediction_confidence = np.median(
            [song.prediction_confidence_score for song in self.data_model.song_objects if not song.is_categorised])
        print(f"Median Prediction Confidence {self.median_prediction_confidence}")

    @staticmethod
    def assess_prediction_confidence(avg_prediction):
        """Before the model had seen any data or knows anything about the distribution of categories, its best guess would be to assign a
        song to one of the n categories with equal likelihood. Therefore, a prediction distribution [1/n, ... , 1/n] represents absolute
        ignorance. Conversely, a distribution with all zeros except for one value of 1 represents perfect learning. The confidence  metric
        computed in this method uses entropy to quantify where a prediction lies on a scale [0, 1] where 0 represents absolute ignorance and
        1 represents perfect learning."""
        # Compute entropy
        entropy = -sum(p * math.log(p) for p in avg_prediction if p > 0)

        # Compute the entropy for a uniform distribution
        n = len(avg_prediction)
        entropy_uniform = math.log(n)

        # Compute the confidence metric
        confidence = (entropy_uniform - entropy) / entropy_uniform

        return confidence

    def assign_song_categories(self):
        for song in self.data_model.song_objects:
            if not song.is_categorised and song.prediction_confidence_score >= prediction_confidence_threshold:
                song.is_categorised = True

                # Encode the predicted category to apply this prediction to use within the training data
                num_rows = song.yamnet_embeddings.shape[0]
                predicted_category_column = np.full((num_rows, 1), song.predicted_category)
                predicted_category_encoded = self.data_model.category_encoder.transform(predicted_category_column)
                song.predicted_category_encoded = predicted_category_encoded

    def investigate_confidence_threshold(self):
        confidence_thresholds = np.linspace(0, 1, num=101)
        uncategorised_songs = [song for song in self.data_model.song_objects if not song.is_categorised]
        results = []
        for threshold in confidence_thresholds:
            songs_above_threshold = [song for song in uncategorised_songs if song.prediction_confidence_score >= threshold]
            correctly_categorised_songs = [song for song in songs_above_threshold if song.predicted_category == song.category]
            results.append({
                "threshold": threshold,
                "perc_songs_above_threshold": len(songs_above_threshold) / len(uncategorised_songs),
                "accuracy": len(correctly_categorised_songs) / len(songs_above_threshold) if len(songs_above_threshold) > 0 else None,
            })
        df = pd.DataFrame(results)

        import matplotlib.pyplot as plt
        import matplotlib

        matplotlib.use('MacOSX')
        plt.ion()

        # Plotting
        plt.figure(figsize=(10, 6))
        plt.plot(df['threshold'], df['perc_songs_above_threshold'], label='perc_songs_above_threshold')
        plt.plot(df['threshold'], df['accuracy'], label='accuracy')

        plt.xlabel('Confidence Threshold')
        plt.legend()  # Adding a legend
        plt.show()  # Displaying the plot

    def manually_categorise_unconfident_songs(self):
        uncategorised_songs = [song for song in self.data_model.song_objects if not song.is_categorised]
        uncategorised_songs.sort(key=operator.attrgetter('prediction_confidence_score'))
        end_index = min(num_manual_per_round, len(uncategorised_songs))
        for song in uncategorised_songs[0:end_index]:
            song.is_root = True
            song.is_categorised = True

        # Update counts of categorised/uncategorised songs
        self.data_model.num_uncategorised_songs = len([song for song in self.data_model.song_objects if not song.is_categorised])
        self.data_model.num_categorised_songs = len([song for song in self.data_model.song_objects if song.is_categorised])


class ClusteringModel(AbstractModel):
    def __init__(self, data_model=None):
        super().__init__(data_model)
        self.num_clusters = self.data_model.num_categories  # math.ceil(len(self.data_model.song_objects) / 5)  #
        self.model = self.configure_model()
        self.model = self.fit_model()

    def configure_model(self):
        kmeans_model = KMeans(n_clusters=self.num_clusters, random_state=0)
        return kmeans_model

    def fit_model(self):
        # List to store song names and their corresponding embeddings
        data = []

        for song in self.data_model.song_objects:
            # Store each song's name and its aggregated YAMNET embeddings in a row
            data.append([song.name] + list(song.aggregated_yamnet_embeddings))

        # Convert to a DataFrame, where the first column is the song name, and the rest are embeddings
        df = pd.DataFrame(data, columns=['song_name'] + [f'embedding_{i}' for i in range(len(song.aggregated_yamnet_embeddings))])

        # Extract the embeddings (i.e., all columns except 'song_name')
        X = df.drop('song_name', axis=1).values

        # Run K-Means clustering on the embeddings
        df['cluster'] = self.model.fit_predict(X)  # Add cluster labels to the DataFrame

        cluster_df = df[['song_name', 'cluster']].sort_values(by=['cluster', 'song_name'])
        return cluster_df
