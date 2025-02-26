from shared.validation import create_response, verify_auth
from shared.mongo_utils import get_item, delete_item
from shared.cloudwatch_logger import setup_logging, logger, log_event, log_api_metrics, metrics
import time

# Set up logging with Lambda Powertools
setup_logging("delete_item")

@metrics.log_metrics  # Add metrics
def handler(event, context):
    start_time = time.time()
    try:
        log_event(event, context)
        logger.info("Processing delete item request")

        # Verify authentication
        is_auth_valid, auth_error = verify_auth(event)
        if not is_auth_valid:
            logger.error(f"Authentication error: {auth_error}")
            status_code = 401
            response = create_response(status_code, {'error': f'Authentication failed: {auth_error}'})
            log_api_metrics("DeleteItem", status_code, (time.time() - start_time) * 1000)
            return response

        item_id = event['pathParameters']['id']

        # Check if item exists
        existing_item = get_item(item_id)
        if not existing_item:
            logger.info(f"Item not found: {item_id}")
            status_code = 404
            response = create_response(status_code, {'error': 'Item not found'})
            log_api_metrics("DeleteItem", status_code, (time.time() - start_time) * 1000)
            return response

        logger.info(f"Deleting item {item_id}")
        delete_item(item_id)

        status_code = 204
        response = create_response(status_code, {})
        log_api_metrics("DeleteItem", status_code, (time.time() - start_time) * 1000)
        return response

    except Exception as e:
        logger.exception("Error deleting item")
        status_code = 500
        response = create_response(status_code, {'error': str(e)})
        log_api_metrics("DeleteItem", status_code, (time.time() - start_time) * 1000)
        return response