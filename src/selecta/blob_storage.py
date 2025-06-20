import os

from tqdm import tqdm
from azure.storage.blob import BlobServiceClient

from selecta.logger import generate_logger

logger = generate_logger()


def create_blob_container_client(storage_account: str, container: str):
    # blob_service_client = BlobServiceClient(
    #     account_url=f"https://{storage_account}.blob.core.windows.net", credential=DefaultAzureCredential()
    # )
    # TODO - Change this to a more secure method
    blob_service_client = BlobServiceClient.from_connection_string(
        "DefaultEndpointsProtocol=https;AccountName=saselecta;AccountKey=DWPPyURtIU2aZG3NFZHErwEENzQYnIlu/yU6Ac4DB/3d66M7XBYaVpwiyq+NuBbPCW15eFg5fabg+ASt4zkyCA==;EndpointSuffix=core.windows.net"
    )
    container_client = blob_service_client.get_container_client(container)

    return container_client


def download_blobs(container_client, prefix: str, local_dir_path: str) -> None:
    try:
        if not os.path.exists(local_dir_path):
            os.makedirs(local_dir_path)

        local_file_paths = []
        blobs = container_client.list_blobs(name_starts_with=prefix)
        for blob in tqdm(blobs):
            blob_name = blob.name
            file_name = os.path.basename(blob_name)  # extract filename from path
            blob_client = container_client.get_blob_client(blob_name)
            download_path = os.path.join(local_dir_path, file_name)
            local_file_paths.extend(download_path)

            with open(download_path, "wb") as f:
                f.write(blob_client.download_blob().readall())
    except Exception as e:
        logger.error(e)


def upload_blob(container_client, local_file_path: str, blob_path: str) -> None:
    blob_client = container_client.get_blob_client(blob_path)

    with open(local_file_path, "rb") as file:
        blob_client.upload_blob(file, overwrite=True)
