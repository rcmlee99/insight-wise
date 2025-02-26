from shared.validation import create_response
from shared.mongo_utils import get_all_items
from shared.cloudwatch_logger import setup_logging, logger, log_event, log_api_metrics, metrics
import time

# Set up logging with Lambda Powertools
setup_logging("get_items")

@metrics.log_metrics  # Add metrics
def handler(event, context):
    start_time = time.time()
    try:
        log_event(event, context)
        logger.info("Processing get items request")

        items = get_all_items()
        status_code = 200
        response = create_response(status_code, {'items': items})
        log_api_metrics("GetItems", status_code, (time.time() - start_time) * 1000)
        return response

    except Exception as e:
        logger.exception("Error getting items")
        status_code = 500
        response = create_response(status_code, {'error': str(e)})
        log_api_metrics("GetItems", status_code, (time.time() - start_time) * 1000)
        return response