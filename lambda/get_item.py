from shared.validation import create_response, verify_auth
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

        # Verify authentication
        is_auth_valid, auth_error = verify_auth(event)
        if not is_auth_valid:
            logger.error(f"Authentication error: {auth_error}")
            status_code = 401
            response = create_response(status_code, {'error': f'Authentication failed: {auth_error}'})
            log_api_metrics("GetItem", status_code, (time.time() - start_time) * 1000)
            return response

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