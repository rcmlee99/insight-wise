# tests/test_handler.py
import pytest
from mongomock import connect as mock_connect
from handler import main, Item
from datetime import datetime, timedelta
import json

# Mock MongoDB connection
mock_connect('item_locations', host='mongomock://localhost')

# Helper function to create event
def create_event(http_method, path, body=None, token='valid-token', postcode='10001'):
    return {
        'httpMethod': http_method,
        'path': path,
        'headers': {
            'Authorization': f'Bearer {token}'
        },
        'body': json.dumps(body) if body else None,
        'queryStringParameters': {
            'postcode': postcode
        }
    }

# Test Cases

def test_missing_bearer_token():
    event = create_event('POST', '/items', token='')
    response = main(event, None)
    assert response['statusCode'] == 401
    assert 'Unauthorized' in response['body']


def test_name_validation():
    event = create_event('POST', '/items', {'name': 'a' * 51})
    response = main(event, None)
    assert response['statusCode'] == 400
    assert 'Name is required and must be less than 50 characters' in response['body']


def test_users_validation():
    event = create_event('POST', '/items', {'name': 'Valid Name', 'users': ['a' * 51]})
    response = main(event, None)
    assert response['statusCode'] == 400
    assert 'All users must be strings and less than 50 characters' in response['body']


def test_start_date_validation():
    start_date = (datetime.now() + timedelta(days=2)).isoformat()
    event = create_event('POST', '/items', {
        'name': 'Valid Name',
        'users': ['John Doe'],
        'startDate': start_date
    })
    response = main(event, None)
    assert response['statusCode'] == 400
    assert 'StartDate must be at least 1 week from today' in response['body']


def test_valid_item_creation(mocker):
    mocker.patch('requests.get').return_value.json.return_value = {
        'places': [{'latitude': '40.7128', 'longitude': '-74.0060'}]
    }
    mocker.patch('requests.get').return_value.status_code = 200
    event = create_event('POST', '/items', {
        'name': 'John Doe',
        'title': 'Engineer',
        'users': ['John Doe', 'Jane Smith'],
        'startDate': (datetime.now() + timedelta(weeks=2)).isoformat()
    })
    response = main(event, None)
    assert response['statusCode'] == 200
    assert 'directionFromNewYork' in response['body']


def test_invalid_postcode(mocker):
    mocker.patch('requests.get').return_value.status_code = 404
    event = create_event('POST', '/items', {'name': 'John Doe'})
    response = main(event, None)
    assert response['statusCode'] == 404
    assert 'Postcode not found' in response['body']
