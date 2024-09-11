from classes.data_model import DataModel
from classes.model import AbstractModel, TransferLearningModel, ClusteringModel

if __name__ == '__main__':
    data_model = DataModel()

    # Clustering Model
    clustering_model = ClusteringModel(data_model=data_model)

    # Transfer Learning Model
    loop_counter = 0
    while data_model.num_uncategorised_songs > 0:  # and loop_counter < 5:
        transfer_learning_model = TransferLearningModel(data_model)
        loop_counter += 1
        print(f"{data_model.num_uncategorised_songs} remaining songs to categorise")
    uncategorised_songs = [song for song in data_model.song_objects if not song.is_categorised]
    for song in uncategorised_songs:
        song.is_categorised = True

    non_root_songs = [song for song in data_model.song_objects if not song.is_root]
    correct_predictions = [song for song in non_root_songs if song.predicted_category == song.category]
    accuracy = len(correct_predictions) / len(non_root_songs) if len(non_root_songs) > 0 else 0
    print(f"Accuracy: {len(correct_predictions)}/{len(non_root_songs)} ({round(100 * accuracy, 2)}%)")
