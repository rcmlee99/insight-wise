from shared.validation import create_response
from shared.mongo_utils import get_item
from shared.cloudwatch_logger import setup_logging, logger, log_event, log_api_metrics, metrics
import time

# Set up logging with Lambda Powertools
setup_logging("get_item")

@metrics.log_metrics  # Add metrics
def handler(event, context):
    start_time = time.time()
    try:
        log_event(event, context)
        logger.info("Processing get item request")

        item_id = event['pathParameters']['id']
        item = get_item(item_id)

        if not item:
            logger.info(f"Item not found: {item_id}")
            status_code = 404
            response = create_response(status_code, {'error': 'Item not found'})
            log_api_metrics("GetItem", status_code, (time.time() - start_time) * 1000)
            return response

        status_code = 200
        response = create_response(status_code, item)
        log_api_metrics("GetItem", status_code, (time.time() - start_time) * 1000)
        return response

    except Exception as e:
        logger.exception("Error getting item")
        status_code = 500
        response = create_response(status_code, {'error': str(e)})
        log_api_metrics("GetItem", status_code, (time.time() - start_time) * 1000)
        return response