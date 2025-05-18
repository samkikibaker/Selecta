import json

from azure.identity import DefaultAzureCredential
from azure.storage.queue import QueueServiceClient

from selecta.SongProcessor import SongProcessor
from selecta.logger import generate_logger

logger = generate_logger()

# {"email": "samkikibaker@hotmail.co.uk"}

try:
    logger.info("Analysing Songs...")

    # Get email of user triggering job
    queue_service_client = QueueServiceClient(
        account_url="https://saselecta.queue.core.windows.net/", credential=DefaultAzureCredential()
    )
    queue_client = queue_service_client.get_queue_client(queue="q-selecta")
    messages = queue_client.receive_messages(max_messages=10)
    message_obj = next(iter(messages))
    # queue_client.delete_message(message_obj.id, message_obj.pop_receipt)
    message = json.loads(message_obj.content)
    user_email = message.get("email")

    song_processor = SongProcessor(user_email)

    logger.info("Analysis Complete!")

except Exception as e:
    logger.error(f"An error occurred: {e}")
    raise e
