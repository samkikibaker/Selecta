import json
import os
import base64

from azure.identity import DefaultAzureCredential
from azure.storage.queue import QueueServiceClient
from azure.storage.blob import BlobServiceClient
from tqdm import tqdm

from selecta.SongCategoriser import SongCategoriser

# Get email of user triggering job
# List all song names from blob storage and download them
# Load or create song objects
# Compute similarity matrix
# Write songs cache and similarity matrix back to blob storage

# TODO - How to avoid recomputing the similarity between existing songs and only compute new vs existing or new vs new?

# Get email of user triggering job
queue_service_client = QueueServiceClient(
    account_url="https://saselecta.queue.core.windows.net/", credential=DefaultAzureCredential()
)
queue_client = queue_service_client.get_queue_client(queue="q-selecta")
messages = queue_client.receive_messages(max_messages=10)
message_obj = next(iter(messages))
# queue_client.delete_message(message_obj.id, message_obj.pop_receipt)
decoded_bytes = base64.b64decode(message_obj.content)
message = json.loads(decoded_bytes.decode("utf-8"))
user_email = message.get("email")

# List all song names from blob storage and then download them
blob_service_client = BlobServiceClient(
    account_url="https://saselecta.blob.core.windows.net", credential=DefaultAzureCredential()
)
container_client = blob_service_client.get_container_client("containerselecta")
prefix = f"users/{user_email}/songs/"
local_song_paths = []
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
