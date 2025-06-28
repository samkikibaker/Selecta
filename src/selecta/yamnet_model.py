from keras.layers import TFSMLayer

from selecta.logger import generate_logger
from selecta.utils import resource_path

logger = generate_logger()

try:
    yamnet_model_path = resource_path("yamnet-tensorflow2-yamnet-v1")
    logger.info(f"Loading YAMNet model from: {yamnet_model_path}")
    yamnet_model = TFSMLayer(str(yamnet_model_path), call_endpoint='serving_default')
except Exception as e:
    logger.error(f"Failed to load YAMNet model: {e}")
    raise e