import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import json
from unittest.mock import patch, MagicMock
from jose import jwt
from datetime import datetime, timedelta
from create_item import handler as create_handler
from get_item import handler as get_handler
from get_items import handler as get_items_handler
from update_item import handler as update_handler
from delete_item import handler as delete_handler
from shared.validation import validate_item

@pytest.fixture
def valid_item():
    return {
        'name': 'Test Item',
        'postcode': '10001',
        'startDate': '2025-03-26T00:00:00Z',
        'users': ['John Doe']
    }

@pytest.fixture
def mock_coordinates():
    return (40.7128, -74.0060)

@pytest.fixture
def mock_token():
    """Create a mock JWT token for testing"""
    claims = {
        'sub': '123',
        'email': 'test@example.com',
        'aud': 'test-client-id',
        'exp': datetime.utcnow() + timedelta(hours=1),
        'iss': f'https://cognito-idp.us-east-1.amazonaws.com/test-pool'
    }
    return jwt.encode(claims, 'test-key', algorithm='HS256')

@pytest.fixture
def mock_event(valid_item, mock_token):
    return {
        'body': json.dumps(valid_item),
        'pathParameters': {'id': '123'},
        'headers': {'Authorization': f'Bearer {mock_token}'}
    }

@patch('create_item.verify_auth')  # Patch at create_item's namespace
@patch('shared.geocoding.get_coordinates')
def test_create_item(mock_get_coordinates, mock_verify_auth, mock_event, mock_coordinates, mongodb_collection):
    # Mock successful coordinates lookup and token verification
    mock_get_coordinates.return_value = mock_coordinates
    mock_verify_auth.return_value = (True, "")  # Return successful auth tuple

    # Test successful creation
    response = create_handler(mock_event, None)
    assert response['statusCode'] == 201

    # Verify item was created with correct fields
    created_item = json.loads(response['body'])
    assert 'id' in created_item
    assert 'latitude' in created_item
    assert 'longitude' in created_item
    assert 'distanceFromNY' in created_item
    assert 'directionFromNY' in created_item

    # Test invalid JSON body
    invalid_event = mock_event.copy()
    invalid_event['body'] = "invalid json"
    response = create_handler(invalid_event, None)
    assert response['statusCode'] == 500

    # Test missing required fields
    invalid_item = {'name': 'Test Item'}
    invalid_event['body'] = json.dumps(invalid_item)
    response = create_handler(invalid_event, None)
    assert response['statusCode'] == 400

def test_get_item(mock_event, mongodb_collection):
    # Create test item
    mongodb_collection.insert_one({
        'id': '123',
        'name': 'Test Item',
        'users': ['John Doe']
    })

    # Mock successful authentication
    with patch('get_item.verify_auth', return_value=(True, "")):
        # Test get existing item
        response = get_handler(mock_event, None)
        assert response['statusCode'] == 200
        item = json.loads(response['body'])
        assert item['name'] == 'Test Item'

        # Test get non-existent item
        mock_event['pathParameters']['id'] = 'non-existent'
        response = get_handler(mock_event, None)
        assert response['statusCode'] == 404

@patch('get_item.verify_auth')
def test_get_item_errors(mock_verify_auth, mock_event, mongodb_collection):
    mock_verify_auth.return_value = (True, "")

    # Test missing path parameters
    invalid_event = mock_event.copy()
    invalid_event.pop('pathParameters')
    response = get_handler(invalid_event, None)
    assert response['statusCode'] == 500

    # Test invalid item ID format
    invalid_event = mock_event.copy()
    invalid_event['pathParameters'] = {'id': 'invalid-id'}
    response = get_handler(invalid_event, None)
    assert response['statusCode'] == 404


def test_get_items(mongodb_collection):
    # Create test items
    items = [
        {'id': '123', 'name': 'Item 1', 'users': ['User 1']},
        {'id': '456', 'name': 'Item 2', 'users': ['User 2']}
    ]
    for item in items:
        mongodb_collection.insert_one(item)

    response = get_items_handler({}, None)
    assert response['statusCode'] == 200
    returned_items = json.loads(response['body'])['items']
    assert len(returned_items) == 2

@patch('shared.geocoding.get_coordinates')
def test_update_item(mock_get_coordinates, mock_event, mock_coordinates, mongodb_collection):
    # Create test item
    mongodb_collection.insert_one({
        'id': '123',
        'name': 'Original Name',
        'users': ['John Doe']
    })

    mock_get_coordinates.return_value = mock_coordinates

    # Mock successful authentication
    with patch('update_item.verify_auth', return_value=(True, "")):
        # Test successful update
        update_data = {
            'name': 'Updated Name',
            'postcode': '10002'
        }
        mock_event['body'] = json.dumps(update_data)

        response = update_handler(mock_event, None)
        assert response['statusCode'] == 200
        updated_item = json.loads(response['body'])
        assert updated_item['name'] == 'Updated Name'

        # Test update non-existent item
        mock_event['pathParameters']['id'] = 'non-existent'
        response = update_handler(mock_event, None)
        assert response['statusCode'] == 404

@patch('update_item.verify_auth')
@patch('shared.geocoding.get_coordinates')
def test_update_item_errors(mock_get_coordinates, mock_verify_auth, mock_event, mock_coordinates, mongodb_collection):
    mock_verify_auth.return_value = (True, "")
    mock_get_coordinates.return_value = mock_coordinates

    # Create test item first
    mongodb_collection.insert_one({
        'id': '123',
        'name': 'Original Name',
        'users': ['John Doe']
    })

    # Test invalid JSON body
    invalid_event = mock_event.copy()
    invalid_event['body'] = "invalid json"
    response = update_handler(invalid_event, None)
    assert response['statusCode'] == 500

    # Test geocoding failure
    mock_get_coordinates.return_value = None
    valid_updates = {'postcode': '99999'}
    mock_event['body'] = json.dumps(valid_updates)
    response = update_handler(mock_event, None)
    assert response['statusCode'] == 400

def test_delete_item(mock_event, mongodb_collection):
    # Create test item
    mongodb_collection.insert_one({
        'id': '123',
        'name': 'Test Item',
        'users': ['John Doe']
    })

    # Mock successful authentication
    with patch('delete_item.verify_auth', return_value=(True, "")):
        # Test successful deletion
        response = delete_handler(mock_event, None)
        assert response['statusCode'] == 204

        # Test delete non-existent item
        mock_event['pathParameters']['id'] = 'non-existent'
        response = delete_handler(mock_event, None)
        assert response['statusCode'] == 404

@patch('delete_item.verify_auth')
def test_delete_item_errors(mock_verify_auth, mock_event, mongodb_collection):
    mock_verify_auth.return_value = (True, "")

    # Test missing path parameters
    invalid_event = mock_event.copy()
    invalid_event.pop('pathParameters')
    response = delete_handler(invalid_event, None)
    assert response['statusCode'] == 500

def test_get_items_errors(mongodb_collection):
    # Test database error by mocking a failure
    with patch('get_items.get_all_items', side_effect=Exception("Database error")):
        response = get_items_handler({}, None)
        assert response['statusCode'] == 500
        error_message = json.loads(response['body'])['error']
        assert "Database error" in error_message

@patch('create_item.verify_auth')  # Patch at create_item's namespace
def test_create_item_unauthorized(mock_verify_auth, mock_event, mongodb_collection):
    # Mock token verification failure
    mock_verify_auth.return_value = (False, "Invalid token")  # Return failed auth tuple

    response = create_handler(mock_event, None)
    assert response['statusCode'] == 401
    error_response = json.loads(response['body'])
    assert 'Authentication failed' in error_response['error']