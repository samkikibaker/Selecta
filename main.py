import json
import os

from azure.identity import DefaultAzureCredential
from azure.storage.queue import QueueServiceClient
from azure.storage.blob import BlobServiceClient
from tqdm import tqdm

from selecta.SongCategoriser import SongCategoriser
from selecta.logger import generate_logger

# Get email of user triggering job
# List all song names from blob storage and download them
# Load or create song objects
# Compute similarity matrix
# Write songs cache and similarity matrix back to blob storage

# TODO - How to avoid recomputing the similarity between existing songs and only compute new vs existing or new vs new?
logger = generate_logger()

try:
    logger.info("Analysing Songs...")

    # Get email of user triggering job
    queue_service_client = QueueServiceClient(
        account_url="https://saselecta.queue.core.windows.net/", credential=DefaultAzureCredential()
    )
    queue_client = queue_service_client.get_queue_client(queue="q-selecta")
    messages = queue_client.receive_messages(max_messages=10)
    message_obj = next(iter(messages))
    queue_client.delete_message(message_obj.id, message_obj.pop_receipt)
    message = json.loads(message_obj.content)
    user_email = message.get("email")

    # List all song names from blob storage and then download them
    blob_service_client = BlobServiceClient(
        account_url="https://saselecta.blob.core.windows.net", credential=DefaultAzureCredential()
    )
    container_client = blob_service_client.get_container_client("containerselecta")
    prefix = f"users/{user_email}/songs/"
    local_song_paths = []
    if not os.path.exists("songs"):
        os.makedirs("songs")
    for blob in tqdm(container_client.list_blobs(name_starts_with=prefix)):
        blob_name = blob.name
        file_name = os.path.basename(blob_name)  # extract filename from path
        blob_client = container_client.get_blob_client(blob_name)
        download_path = os.path.join("songs", file_name)
        local_song_paths.extend(download_path)
        with open(download_path, "wb") as f:
            f.write(blob_client.download_blob().readall())

    # Load or create song objects & Compute similarity matrix
    song_categoriser = SongCategoriser("songs")

    # Write songs cache and similarity matrix back to blob storage
    blob_client_similarity_matrix = container_client.get_blob_client(
        f"users/{user_email}/cache/{song_categoriser.similarity_matrix_cache_filename}"
    )
    with open(f"cache/{song_categoriser.similarity_matrix_cache_filename}", "rb") as data:
        blob_client_similarity_matrix.upload_blob(data, overwrite=True)

    blob_client_songs = container_client.get_blob_client(
        f"users/{user_email}/cache/{song_categoriser.songs_cache_filename}"
    )
    with open(f"cache/{song_categoriser.songs_cache_filename}", "rb") as data:
        blob_client_songs.upload_blob(data, overwrite=True)

    logger.info("Analysis Complete!")

except Exception as e:
    logger.error(f"An error occurred: {e}")
    raise e
