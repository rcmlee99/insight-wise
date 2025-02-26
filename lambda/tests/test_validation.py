import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from datetime import datetime, timedelta
from shared.validation import validate_item, validate_users, validate_name_length

def test_validate_name_length():
    assert validate_name_length("Valid Name") == True
    assert validate_name_length("A" * 50) == False
    assert validate_name_length("") == True

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

    # Invalid user name length
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