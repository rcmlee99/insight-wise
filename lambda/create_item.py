import json
import uuid
import time
from shared.validation import validate_item, create_response, verify_auth
from shared.geocoding import get_coordinates, calculate_distance_from_ny, get_direction_from_ny
from shared.mongo_utils import create_item
from shared.cloudwatch_logger import setup_logging, logger, log_event, log_api_metrics, metrics

# Set up logging with Lambda Powertools
setup_logging("create_item")

@metrics.log_metrics  # Add metrics
def handler(event, context):
    start_time = time.time()
    try:
        log_event(event, context)
        logger.info("Processing create item request")

        # Verify authentication
        is_auth_valid, auth_error = verify_auth(event)
        if not is_auth_valid:
            logger.error(f"Authentication error: {auth_error}")
            status_code = 401
            response = create_response(status_code, {'error': f'Authentication failed: {auth_error}'})
            log_api_metrics("CreateItem", status_code, (time.time() - start_time) * 1000)
            return response

        body = json.loads(event['body'])

        # Validate input
        is_valid, error_message = validate_item(body)
        if not is_valid:
            logger.error(f"Validation error: {error_message}")
            status_code = 400
            response = create_response(status_code, {'error': error_message})
            log_api_metrics("CreateItem", status_code, (time.time() - start_time) * 1000)
            return response

        # Get coordinates from postcode
        coordinates = get_coordinates(body['postcode'])
        if not coordinates:
            logger.error("Invalid postcode: Could not get coordinates")
            status_code = 400
            response = create_response(status_code, {'error': 'Invalid postcode'})
            log_api_metrics("CreateItem", status_code, (time.time() - start_time) * 1000)
            return response

        lat, lon = coordinates
        distance_from_ny = calculate_distance_from_ny(lat, lon)
        direction_from_ny = get_direction_from_ny(lat, lon)

        # Create item with additional data
        item = {
            'id': str(uuid.uuid4()),
            **body,
            'latitude': float(lat),
            'longitude': float(lon),
            'distanceFromNY': float(distance_from_ny),
            'directionFromNY': direction_from_ny
        }

        logger.info("Creating item in MongoDB", extra={"item": item})
        create_item(item)

        status_code = 201
        response = create_response(status_code, item)
        log_api_metrics("CreateItem", status_code, (time.time() - start_time) * 1000)
        return response

    except Exception as e:
        logger.exception("Error creating item")
        status_code = 500
        response = create_response(status_code, {'error': str(e)})
        log_api_metrics("CreateItem", status_code, (time.time() - start_time) * 1000)
        return response