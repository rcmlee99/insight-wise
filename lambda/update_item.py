import json
from shared.validation import create_response, verify_auth
from shared.geocoding import get_coordinates, calculate_distance_from_ny, get_direction_from_ny
from shared.mongo_utils import get_item, update_item
from shared.cloudwatch_logger import setup_logging, logger, log_event, log_api_metrics, metrics
import time

# Set up logging with Lambda Powertools
setup_logging("update_item")

@metrics.log_metrics  # Add metrics
def handler(event, context):
    start_time = time.time()
    try:
        log_event(event, context)
        logger.info("Processing update item request")

        # Verify authentication
        is_auth_valid, auth_error = verify_auth(event)
        if not is_auth_valid:
            logger.error(f"Authentication error: {auth_error}")
            status_code = 401
            response = create_response(status_code, {'error': f'Authentication failed: {auth_error}'})
            log_api_metrics("UpdateItem", status_code, (time.time() - start_time) * 1000)
            return response

        item_id = event['pathParameters']['id']
        updates = json.loads(event['body'])

        # Check if item exists
        existing_item = get_item(item_id)
        if not existing_item:
            logger.info(f"Item not found: {item_id}")
            status_code = 404
            response = create_response(status_code, {'error': 'Item not found'})
            log_api_metrics("UpdateItem", status_code, (time.time() - start_time) * 1000)
            return response

        # If postcode is being updated, recalculate coordinates and directions
        if 'postcode' in updates:
            coordinates = get_coordinates(updates['postcode'])
            if not coordinates:
                logger.error("Invalid postcode")
                status_code = 400
                response = create_response(status_code, {'error': 'Invalid postcode'})
                log_api_metrics("UpdateItem", status_code, (time.time() - start_time) * 1000)
                return response

            lat, lon = coordinates
            updates['latitude'] = float(lat)
            updates['longitude'] = float(lon)
            updates['distanceFromNY'] = float(calculate_distance_from_ny(lat, lon))
            updates['directionFromNY'] = get_direction_from_ny(lat, lon)

        # Update item
        logger.info(f"Updating item {item_id}", extra={"updates": updates})
        update_item(item_id, updates)

        # Get updated item
        updated_item = get_item(item_id)
        status_code = 200
        response = create_response(status_code, updated_item)
        log_api_metrics("UpdateItem", status_code, (time.time() - start_time) * 1000)
        return response

    except Exception as e:
        logger.exception("Error updating item")
        status_code = 500
        response = create_response(status_code, {'error': str(e)})
        log_api_metrics("UpdateItem", status_code, (time.time() - start_time) * 1000)
        return response