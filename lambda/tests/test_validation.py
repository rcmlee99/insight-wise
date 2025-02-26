import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from datetime import datetime, timedelta
import json
from decimal import Decimal
from bson import ObjectId
from shared.validation import (
    validate_name_length,
    validate_users,
    validate_item,
    create_response,
    DecimalEncoder,
    verify_auth,
    get_token_from_event
)

def test_decimal_encoder():
    # Test Decimal encoding
    decimal_data = {'amount': Decimal('10.99')}
    encoded = json.dumps(decimal_data, cls=DecimalEncoder)
    assert json.loads(encoded)['amount'] == 10.99

    # Test ObjectId encoding
    obj_id = ObjectId()
    obj_data = {'id': obj_id}
    encoded = json.dumps(obj_data, cls=DecimalEncoder)
    assert json.loads(encoded)['id'] == str(obj_id)

    # Test default encoding
    data = {'date': datetime.now()}
    with pytest.raises(TypeError):
        json.dumps(data, cls=DecimalEncoder)

def test_validate_name_length():
    assert validate_name_length("Valid Name") == True
    assert validate_name_length("A" * 50) == False
    assert validate_name_length("") == True
    assert validate_name_length("A" * 49) == True

def test_validate_users():
    # Valid users list
    valid_users = ["John Doe", "Jane Smith"]
    is_valid, error = validate_users(valid_users)
    assert is_valid == True
    assert error == ""

    # Empty users list
    is_valid, error = validate_users([])
    assert is_valid == False
    assert "cannot be empty" in error

    # Invalid type
    is_valid, error = validate_users("not a list")
    assert is_valid == False
    assert "must be a list" in error

    # Invalid user name
    is_valid, error = validate_users([123])
    assert is_valid == False
    assert "must be a string" in error

    # Invalid name length
    long_name = "A" * 51
    is_valid, error = validate_users(["John Doe", long_name])
    assert is_valid == False
    assert "exceeds 50 characters" in error

def test_validate_item():
    # Valid item
    valid_item = {
        'name': 'Test Item',
        'postcode': '10001',
        'startDate': (datetime.now() + timedelta(weeks=2)).isoformat(),
        'users': ['John Doe', 'Jane Smith']
    }
    is_valid, error = validate_item(valid_item)
    assert is_valid == True
    assert error == ""

    # Missing required field
    invalid_item = {
        'name': 'Test Item',
        'postcode': '10001',
        'users': ['John Doe']
    }
    is_valid, error = validate_item(invalid_item)
    assert is_valid == False
    assert "Missing required field" in error

    # Invalid name length
    invalid_item = {
        'name': 'A' * 51,
        'postcode': '10001',
        'startDate': (datetime.now() + timedelta(weeks=2)).isoformat(),
        'users': ['John Doe']
    }
    is_valid, error = validate_item(invalid_item)
    assert is_valid == False
    assert "Name must be less than 50 characters" in error

    # Start date too soon
    invalid_date_item = {
        'name': 'Test Item',
        'postcode': '10001',
        'startDate': datetime.now().isoformat(),
        'users': ['John Doe']
    }
    is_valid, error = validate_item(invalid_date_item)
    assert is_valid == False
    assert "at least 1 week from now" in error

    # Invalid date format
    invalid_date_item['startDate'] = 'not a date'
    is_valid, error = validate_item(invalid_date_item)
    assert is_valid == False
    assert "Invalid date format" in error

def test_create_response():
    # Test successful response
    response = create_response(200, {'message': 'Success'})
    assert response['statusCode'] == 200
    assert 'message' in json.loads(response['body'])
    assert response['headers']['Content-Type'] == 'application/json'

    # Test error response
    response = create_response(400, {'error': 'Bad Request'})
    assert response['statusCode'] == 400
    assert 'error' in json.loads(response['body'])

def test_get_token_from_event():
    # Valid token
    event = {
        'headers': {
            'Authorization': 'Bearer valid-token'
        }
    }
    assert get_token_from_event(event) == 'valid-token'

    # Missing Authorization header
    with pytest.raises(ValueError) as exc:
        get_token_from_event({})
    assert "No Authorization header present" in str(exc.value)

    # Invalid Authorization format
    event['headers']['Authorization'] = 'NotBearer token'
    with pytest.raises(ValueError) as exc:
        get_token_from_event(event)
    assert "Invalid Authorization header format" in str(exc.value)

def test_verify_auth():
    # Test missing Authorization header
    event = {}
    is_valid, error = verify_auth(event)
    assert not is_valid
    assert "No Authorization header present" in error

    # Test invalid token format
    event = {'headers': {'Authorization': 'NotBearer token'}}
    is_valid, error = verify_auth(event)
    assert not is_valid
    assert "Invalid Authorization header format" in error

    # Test invalid token
    event = {'headers': {'Authorization': 'Bearer invalid-token'}}
    is_valid, error = verify_auth(event)
    assert not is_valid
    assert "Invalid token" in error