from flask import request, jsonify
from app import app
from shared.validation import validate_item, verify_auth
from shared.mongo_utils import create_item, get_item, get_all_items, update_item, delete_item
from shared.geocoding import get_coordinates, calculate_distance_from_ny, get_direction_from_ny
import uuid

@app.route('/items', methods=['POST'])
def create_item_route():
    try:
        # Verify authentication
        is_auth_valid, auth_error = verify_auth(request)
        if not is_auth_valid:
            return jsonify({'error': f'Authentication failed: {auth_error}'}), 401

        data = request.get_json()
        
        # Validate input
        is_valid, error_message = validate_item(data)
        if not is_valid:
            return jsonify({'error': error_message}), 400

        # Get coordinates from postcode
        coordinates = get_coordinates(data['postcode'])
        if not coordinates:
            return jsonify({'error': 'Invalid postcode'}), 400

        lat, lon = coordinates
        distance_from_ny = calculate_distance_from_ny(lat, lon)
        direction_from_ny = get_direction_from_ny(lat, lon)

        # Create item with additional data
        item = {
            'id': str(uuid.uuid4()),
            **data,
            'latitude': float(lat),
            'longitude': float(lon),
            'distanceFromNY': float(distance_from_ny),
            'directionFromNY': direction_from_ny
        }

        create_item(item)
        return jsonify(item), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/items', methods=['GET'])
def get_items_route():
    try:
        items = get_all_items()
        return jsonify({'items': items}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/items/<item_id>', methods=['GET'])
def get_item_route(item_id):
    try:
        item = get_item(item_id)
        if not item:
            return jsonify({'error': 'Item not found'}), 404
        return jsonify(item), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/items/<item_id>', methods=['PATCH'])
def update_item_route(item_id):
    try:
        # Verify authentication
        is_auth_valid, auth_error = verify_auth(request)
        if not is_auth_valid:
            return jsonify({'error': f'Authentication failed: {auth_error}'}), 401

        updates = request.get_json()
        
        # Check if item exists
        existing_item = get_item(item_id)
        if not existing_item:
            return jsonify({'error': 'Item not found'}), 404

        # If postcode is being updated, recalculate coordinates
        if 'postcode' in updates:
            coordinates = get_coordinates(updates['postcode'])
            if not coordinates:
                return jsonify({'error': 'Invalid postcode'}), 400

            lat, lon = coordinates
            updates['latitude'] = float(lat)
            updates['longitude'] = float(lon)
            updates['distanceFromNY'] = float(calculate_distance_from_ny(lat, lon))
            updates['directionFromNY'] = get_direction_from_ny(lat, lon)

        update_item(item_id, updates)
        updated_item = get_item(item_id)
        return jsonify(updated_item), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/items/<item_id>', methods=['DELETE'])
def delete_item_route(item_id):
    try:
        # Verify authentication
        is_auth_valid, auth_error = verify_auth(request)
        if not is_auth_valid:
            return jsonify({'error': f'Authentication failed: {auth_error}'}), 401

        # Check if item exists
        existing_item = get_item(item_id)
        if not existing_item:
            return jsonify({'error': 'Item not found'}), 404

        delete_item(item_id)
        return '', 204

    except Exception as e:
        return jsonify({'error': str(e)}), 500
